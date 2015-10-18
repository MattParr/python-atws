from distutils.core import setup
setup(
  name = 'atws',
  packages = ['atws'],
  version = '0.1',
  install_requires=[
        'requests',
        'json',
        'pytz',
        'suds>=0.7.dev0'
    ],
  dependency_links = ['hg+https://bitbucket.org/jurko/suds/master/@tip#egg=suds-0.7.dev0'],
  description = 'An Autotask API wrapper',
  author = 'Matt Parr',
  author_email = 'matt@parr.geek.nz',
  url = 'https://github.com/mattparr/python-atws',
  download_url = 'https://github.com/mattparr/python-atws/tarball/0.1',
  keywords = ['autotask', 'soap', 'api'],
  classifiers = [],
)