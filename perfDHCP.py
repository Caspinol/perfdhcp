import sys, argparse, threading, multiprocessing
from Queue import Queue
from client import Client, generate_mac

class ThisThread(threading.Thread):
    def __init__(self, client, q):
        threading.Thread.__init__(self)
        self.client = client
        self.q = q

    def run(self):
        self.client.test_dhcp(self.q)
    
def main(argv):

    queue = Queue()
    thread_num = multiprocessing.cpu_count()
    threads = []
    macnumber = 0
    server = None

    parser = argparse.ArgumentParser(prog='perfDHCP',
                                     usage="\n%(prog)s -m 10 -s 255.255.255.255\n\tor\n"
                                     "cat mac_list.txt | %(prog)s -s 255.255.255.255\n\tor\n"
                                     "%(prog)s -m 10 > mac_list.txt")
    parser.add_argument('--macgen', '-m', type=int, metavar='x',
                        help='Generate "x" random mac addresses')
    parser.add_argument('--server', '-s', metavar='x.x.x.x',
                        help='DHCP server to test or \'255.255.255.255\' for broadcast')
    parser.add_argument('--workers', '-w', type=int, metavar='x', 
                        help='Number of workers (default: CPU count)')
    args = parser.parse_args()

    if(args.server):
        server = args.server
    
    if(args.macgen):
        macnumber = args.macgen

    if server:
        if args.workers:
            thread_num = args.workers

        client = Client(server)
        # Create and start the threads
        for t in xrange(thread_num):
            t = ThisThread(client, queue)
            t.start()
            threads.append(t)
        # Start generating the macs
        # If number was give easy...
        if macnumber > 0:
            for x in xrange(macnumber):
                queue.put(generate_mac(), True, None)
        else:
            # Check if macs given from stdin
            if not sys.stdin.isatty():
                for mac in sys.stdin:
                    queue.put(mac, True, None)
            else:
                print "No mac list given"
                args.print_help()
                sys.exit(1)
        # Wait for all threads to complete
        queue.join()
        client.kill_test()
        print client.show_summary()
        for t in threads:
            t.join()

        sys.exit(0)
            
    if macnumber and not server:
        for x in xrange(macnumber):
            print generate_mac()
        sys.exit(0)

if __name__== "__main__":
    main(sys.argv[1:])
