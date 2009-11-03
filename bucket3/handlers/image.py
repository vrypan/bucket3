from bucket3.bucket import bucket

import codecs
import sys,os
import yaml
from datetime import datetime
import time
import shutil

from django.template import Template, Context, loader

class image(bucket):
	@classmethod
	def types(cls):
		return ('.jpeg','.jpg','.gif')

	def toHTML(cls, content):
		return content

	def __init__(self, conf, file):
		bucket.__init__(self, conf)
		self.file = file
		self.frontmatter = {}

	def parse(self):
		self.page = {}
		img_ts = os.path.getmtime(self.file)
		self.page['cre_dat'] = datetime.fromtimestamp(img_ts)
		self.page['title'] = self.osItemName(self.file)
		self.page['body'] = '<img src="%s/%s" />' % (self.itemURL(file=self.file, cre_dat=self.page['cre_dat']), 
				self.file.split('/')[-1])
		return self

	def title(self):
		return self.page['title']
	def url(self):
		return self.itemURL(file=self.file, cre_dat=self.page['cre_dat'])
	def body(self):
		return self.page['body']
	def date(self):
		return self.page['cre_dat']

	def render(self):
		t = loader.get_template('post.html') 
		c = Context({'blog':self.conf, 'page':self.page, 'frontmatter':self.frontmatter })
		html = t.render(c).encode('utf-8')
		post_dir = self.osItemDir(file=self.file, cre_dat=self.date())
		if not os.path.exists(post_dir):
			os.makedirs(post_dir)
		out_filename = self.osItem(file=self.file, cre_dat=self.date())
		out_file = open(out_filename,'w')
		out_file.write(html)
		out_file.close()
		shutil.copy(self.file, post_dir)


