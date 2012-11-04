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
    url='http://www.bucket3.com/',
    license='MIT-LICENSE.txt',
    description='Static blog generator.',
    long_description=open('README.txt').read(),
    install_requires=[
        "markdown2",
		"Jinja2",
		"PyYAML",
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
         'Environment :: Console',
         'License :: OSI Approved :: MIT License',
         'Operating System :: OS Independent',
         'Programming Language :: Python :: 2.6',
         'Programming Language :: Python :: 2.7',
         'Topic :: Internet :: WWW/HTTP',
         'Topic :: Software Development :: Libraries :: Python Modules',
    ],

)
