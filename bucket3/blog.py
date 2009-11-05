import codecs
import sys,os
import yaml
from datetime import datetime
import time
import sqlite3
from django.template import Template, Context, loader

from bucket3.bucket import bucket
from bucket3.post import post

""" Dynamically import all handlers and register them.
    Is this the right way to do this? 
"""
import bucket3.handlers
from bucket3.handlers import *
for h in bucket3.handlers.__all__:
	m = getattr(bucket3.handlers, h)
	c = getattr(m,h)
	post.regHandler(c)

class blog(bucket):
	def __init__(self,conf):
		bucket.__init__(self,conf)
		self.db_conn = sqlite3.connect(
			conf['db_file'],
			detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES
			)
		self.db_conn.row_factory = sqlite3.Row
		self.db_cur = self.db_conn.cursor()

	def addPost(self,filename):
		c = post(filepath=filename, db_cur=self.db_cur, db_conn=self.db_conn, conf=self.conf)
		if c.handler:
			if not c.in_db():
				print 'Parsing: %s' % filename
				c.parse()
				c.to_db()
				c.render()
		else:
			if os.path.isdir(filename):
				self.walkContentDir(filename)


	def walkContentDir(self,dir):
		for file in os.listdir(dir):
			filename = "%s/%s" % (dir,file)
			self.addPost(filename)

	def updPosts(self):
		self.walkContentDir(self.conf['contentDir'])

	def updIndex(self):
		self.db_cur.execute("SELECT COUNT(*) FROM post")
		res = self.db_cur.fetchall()
		postsNum = res[0][0]
		self.db_cur.execute("SELECT * FROM post WHERE type != 'none' ORDER BY cre_date DESC")
		dbposts = self.db_cur.fetchmany(size=10)
		pagenum = 0

		while dbposts:
			posts = []
			for post in dbposts:
				posts.append({
					'title':post['title'], 
					'body':post['body'],
					'cre_date':post['cre_date'],
					'url':post['url']})

			if (pagenum+1)*10 < postsNum:
				prevPage = pagenum+1
			else:
				prevPage = None
	
			if pagenum>0:
				nextPage = pagenum-1
			else:
				nextPage = None

			if pagenum:
				filename = "index_%s.html" % pagenum
			else:
				filename = "index.html"


			page = {'title':'home', 'pagenum':pagenum,
					'prevPage':prevPage,
					'nextPage':nextPage
					}

			t = loader.get_template('index.html') 
			c = Context({'posts':posts, 'blog':self.conf, 'page':page })
			indexhtml = "%s/%s" % (self.conf['htmlDir'], filename)
			f = open(indexhtml,'w')
			f.write(t.render(c).encode('utf8'))
			f.close()
			dbposts = self.db_cur.fetchmany(size=10)
			pagenum = pagenum+1


