from bucket import bucket

import markdown2
import codecs
import sys,os
import yaml
from datetime import datetime
import time
import sqlite3
import pickle

from django.template import Template, Context, loader

class post(bucket):
	datatypes = {}
	@classmethod
	def regHandler(cls, handler):
		for extension in handler.types():
			cls.datatypes[extension] = handler

	def __init__(self, filepath, conf, db_cur=None, db_conn=None):
		bucket.__init__(self,conf)
		self.debug = False
		self.filepath = filepath
		if not db_cur or not db_conn:
			self.db_conn = sqlite3.connect( 
					conf['db_file'], 
					detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
			self.db_conn.row_factory = sqlite3.Row
			self.db_cur = db_conn.cursor()
		else:
			self.db_conn = db_conn
			self.db_cur = db_cur

		ext = os.path.splitext(self.filepath)[1]
		#print 'DEBUG:', ext, self.datatypes.keys(), filepath
		if ext in self.datatypes:
			self.handler = self.datatypes[ext](conf=conf, file=filepath)
		else:
			self.handler= None

	def parse(self):
		self.handler.parse()

	def render(self):
		self.handler.render()

	def in_db(self):
		src = (self.filepath,)
		src_ts = os.path.getmtime(self.filepath)
		self.db_cur.execute("SELECT * FROM post WHERE src=?",src)
		row = self.db_cur.fetchone()
		if not row:
			return False
		else:
			if row['sys_upd']<src_ts:
				self.db_cur.execute("DELETE FROM post WHERE src=?",src)
				self.db_conn.commit()
				return False
			else:
				return row

	def to_db(self):
		vals = (self.handler.title(),
				self.handler.url(),
				self.handler.body(),
				self.handler.date(),
				time.time(),
				self.filepath,
				pickle.dumps(self.handler.frontmatter))
		self.db_cur.execute("INSERT INTO post(title,url,body,cre_date,sys_upd,src,frontmatter) VALUES(?,?,?,?,?,?,?)", vals)
		self.db_conn.commit()


