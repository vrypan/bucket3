from bucket3.bucket import bucket

import os
from datetime import datetime
import time
import shutil

class dir_static(bucket):
	""" This is a special handler used to copy a static directory
	(usually containing .css, .js etc. files to <baseURL>/static

	It doesn't work as expected. Need to rethink.
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
	def type(self):
		return "none"
	def tags(self):
		return ()

	def render(self):
		post_dir = "%s/%s" % (self.conf['htmlDir'], self.osItemName(self.file) )
		shutil.rmtree(path=post_dir, ignore_errors=True)
		shutil.copytree(self.file, post_dir)
