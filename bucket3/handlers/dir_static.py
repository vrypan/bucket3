from bucket3.bucket import bucket

import os
from datetime import datetime
import time
import shutil

class dir_static(bucket):
	""" This is a special handler used to copy a static directory
	(usually containing .css, .js etc. files to <baseURL>/static
	"""
	@classmethod
	def types(cls):
		return ('.static',)

	def toHTML(self, content):
		return 'static files'

	def __init__(self, conf, file):
		bucket.__init__(self, conf)
		self.file = file
		self.page = {}

	def parse(self):
		self.frontmatter = {}
		self.page['cre_dat'] = datetime.today()
		self.page['title'] = 'static files'
		self.page['body'] = self.toHTML('')
		return self

	def title(self):
		return self.page['title']
	def url(self):
		return "%s/%s" % (self.conf['baseURL'], 'static')
	def body(self):
		return self.page['body']
	def date(self):
		return self.page['cre_dat']

	def render(self):
		post_dir = "%s/%s" % (self.conf['htmlDir'], 'static')
		if not os.path.exists(post_dir):
			os.makedirs(post_dir)
		base, dirs, files = os.walk(self.file).next() 
		for f in files:
			ff = '%s/%s' % (self.file, f)
			shutil.copy(ff, post_dir)
			print 'Copied', ff
		for f in dirs:
			ff = '%s/%s' % (self.file, f)
			shutil.copytree(ff, post_dir)
		print 'Wrote:', out_filename

