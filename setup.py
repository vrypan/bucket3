from setuptools import setup
import os, sys

setup(
    name='bucket3',
    version='0.8.0',
    author='Panayotis Vryonis',
    author_email='vrypan@gmail.com',
    packages=['bucket3'],
    scripts=['bin/bucket3'],
    package_dir={'bucket3': 'bucket3'},
    include_package_data=True,
    url='http://pypi.python.org/pypi/Bucket3/',
    license='MIT-LICENSE.txt',
    description='Static blog generator.',
    long_description=open('README.txt').read(),
    install_requires=[
        "markdown2",
		"Jinja2",
		"PyYAML",
    ],
)
