#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
From v0.9.8 to 0.9.9, URLs changed from single digit month and day,
to double digit.

0.9.8 would create URLs like /2013/1/9/slug/
0.9.9 will create /2013/01/09/slug/

This script will print out a mapping <old path> <new path>
that can be used to create redirects from the old URL structure
to the new one.

If you host your bucket3 blog on amazon S3, check out 
https://github.com/nathangrigg/s3redirect

(It's also a simple example on how to import and use bucket3 
in your own scripts.)

"""

from bucket3 import b3tools
from bucket3 import Bucket3v2 as Bucket3

if __name__ == '__main__':

	conf = b3tools.conf_get('.')
	b = Bucket3(conf = conf)

	for p in b.db_post_get_all(count=0): #count=0 means ALL posts

		url = p['meta']['url']
		date = p['meta']['date']
		slug = p['meta']['slug']

		root_path = '/'.join(b.root_url.split('/')[3:]) # remove http://hostname/ from root_url

		old_path = "/%s%s/%s/%s/%s/" % (
		root_path,
		str(date.year),
		str(date.month),
		str(date.day),
		slug)

		new_path = "/%s%s/%s/%s/%s/" % (
		root_path,
		str(date.year),
		str('{:02d}'.format(date.month)),
		str('{:02d}'.format(date.day)),
		slug)

		if old_path != new_path: 
			print old_path, new_path
