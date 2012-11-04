from setuptools import setup
# from distutils.core import setup
import os, sys

data_files_list = []
rootdir = 'bucket3/_themes'

for root, subFolders, files in os.walk(rootdir):
    #data_files_list.append(root)
    for file in files:
        data_files_list.append(os.path.join(root,file))

setup(
    name='bucket3',
    version='0.8.0',
    author='Panayotis Vryonis',
    author_email='vrypan@gmail.com',
    packages=['bucket3'],
    scripts=['bin/bucket3'],
    package_dir={'bucket3': 'bucket3'},
    # package_data = { 'bucket3' : data_files_list }, 
    # data_files = data_files_list,
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
