#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'click>=6.0',
    'requests',
    'pytz',
    'suds-jurko',
    'future',
    'cached_property'
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='atws',
    version='0.4.2',
    description="python-atws is a wrapper for the AutoTask SOAP webservices API",
    long_description=readme + '\n\n' + history,
    author="Matt Parr",
    author_email='matt@parr.geek.nz',
    url='https://github.com/MattParr/python-atws',
    packages=[
        'atws',
        'atws.monkeypatch'
    ],
    package_dir={'atws':
                 'atws'},
    entry_points={
        'console_scripts': [
            'create_picklist_module=atws.create_picklist_module:main'
        ]
    },
    include_package_data=True,
    install_requires=requirements,
    license="MIT license",
    zip_safe=False,
    keywords='atws Autotask API SOAP',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
