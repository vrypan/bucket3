from setuptools import setup
import os
import sys

from bucket3 import __version__

setup(
    name="bucket3",
    version=__version__,
    author='Panayotis Vryonis',
    author_email='vrypan@gmail.com',
    packages=['bucket3'],
    scripts=['bin/bucket3'],
    package_dir={'bucket3': 'bucket3'},
    include_package_data=True,
    url='http://www.bucket3.com/',
    license='MIT-LICENSE.txt',
    description='Static blog generator.',
    long_description=open('README.rst').read(),
    long_description_content_type='text/x-rst',
    install_requires=[
        "markdown",
        "py-gfm",
        "Jinja2",
        "PyYAML",
        "docopt",
        "unidecode",
        "htmlmin",
        "lxml",
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],

)
