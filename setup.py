try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


config = [
    'description': 'test DHCP server performance',
    'author': 'Kris',
    'version': '0.0.1',
    'name': 'perfDHCP'
]

setup(**config)
