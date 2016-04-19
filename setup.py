from distutils.core import setup
setup(
  name = 'atws',
  scripts=['src/create_picklist_module.py'],
  packages = ['atws','atws.monkeypatch'],
  version = '0.1.4',
  install_requires=[
        'requests',
        'pytz',
        'suds-jurko',
    ],
  description = 'An Autotask API wrapper',
  author = 'Matt Parr',
  author_email = 'matt@parr.geek.nz',
  url = 'https://github.com/mattparr/python-atws',
  download_url = 'https://github.com/mattparr/python-atws/tarball/0.1',
  keywords = ['autotask', 'soap', 'api'],
  classifiers = [],
)
