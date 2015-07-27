#from distutils.core import setup

__version__ = '0.1.1'


METADATA = dict(
    name = 'pygmaps',
    version = __version__,
    py_modules = ['pygmaps'],
    description = 'Python wrapper for Google MAPs javascript API 3.0 ',
    long_description = '',
    license='Apache License 2.0',
    author = 'Yifei Jiang',
    author_email = 'jiangyifei@gmail.com',
    url = 'http://code.google.com/p/pygmaps/',
    keywords='Python wrapper Google Maps',

)


SETUPTOOLS_METADATA = dict(
  include_package_data = True,

)

try:
    import setuptools
    METADATA.update(SETUPTOOLS_METADATA)
    setuptools.setup(**METADATA)
except ImportError:
    import distutils.core
    distutils.core.setup(**METADATA)
