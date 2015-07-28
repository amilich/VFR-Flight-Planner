from setuptools import setup
from __init__ import __version__


setup(name='geocode',
      version=__version__,
      description='simple Python geocoding module using the Google Maps API',
      author='Ben Morris',
      author_email='ben@bendmorris.com',
      url='https://github.com/bendmorris/python-geocode',
      packages=['geocode'],
      package_dir={
                   'geocode':''
                   },
      )
