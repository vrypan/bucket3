from bucket import bucket

import markdown
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
		if not db_conn:
			self.db_conn = sqlite3.connect( 
					self.conf['db_file'], 
					detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
			self.db_conn.row_factory = sqlite3.Row
		else:
			self.db_conn = db_conn

		if not db_cur:
			self.db_cur = self.db_conn.cursor()
		else:
			self.db_cur = db_cur

		ext = os.path.splitext(self.filepath)[1]
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
			self.db_cur.close()
			return False
		else:
			if row['sys_upd']<src_ts:
				self.db_cur.execute("DELETE FROM post_tags WHERE post_id=?",(row['id'],) )
				self.db_cur.execute("DELETE FROM post WHERE ID=?",(row['id'],) )
				self.db_conn.commit()
				self.db_cur.close()
				return False
			else:
				ret = {}
				for x in row.keys():
					ret[x] = row[x]
				self.db_cur.execute("SELECT * FROM post_tags WHERE post_id=?",(row['id'], ))
				ret['tags'] = [ ptag['tag'].strip() for ptag in self.db_cur.fetchall() ]
				post_dict = dict(ret)
				self.db_cur.close()
				return post_dict

	def to_db(self):
		vals = (self.handler.title().strip(),
				self.handler.url(),
				self.handler.body(),
				self.handler.date(),
				time.time(),
				self.filepath,
				pickle.dumps(self.handler.frontmatter),
				self.handler.type(),
				)
		self.db_cur.execute("INSERT INTO post(title,url,body,cre_date,sys_upd,src,frontmatter,type) VALUES(?,?,?,?,?,?,?,?)", vals)
		post_id = self.db_cur.lastrowid
		for tag in self.handler.tags():
			self.db_cur.execute("INSERT INTO post_tags (post_id,tag) VALUES(?,?)", (post_id, tag.strip()) )
		self.db_conn.commit()
