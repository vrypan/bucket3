# -*- coding: utf-8 -*-
# Copyright: 2009 Panayotis Vryonis
# License: GPL

""" Usage: python bucket3.py [OPTIONS] 

OPTIONS:
	-i or --init
	-g or --generate
	--update-index: Reads cache and recreates index pages
	--clear-db: Deletes everything from cache, recreates tables, etc.
	--clear-html: Deletes all files under the htmlDir (as defined in conf.yaml)
	--add-post=<path>: Parses files under <path>. <path> may be a single file, 
					or a directory. <path> must be relative to contentDir 
					as defined in conf.yaml
"""

import markdown2
import codecs
import sys,os
import yaml
from datetime import datetime
import time
import sqlite3
import getopt
import shutil

from bucket3.bucket import bucket
from bucket3.post import post
from bucket3.blog import blog

from django.conf import settings

def main(*argv):
	try:
		(opts,args) = getopt.getopt(argv[1:], 
				'gi',
				['generate', 
					'init', 
					'update-index', 
					'add-post=', 
					'clear-html', 
					'clear-db', 
					])
	except getopt.GetoptError, e:
		print e
		print __doc__
		return 1

	conf = yaml.load(open('./conf.yaml',mode='r').read())

	settings.configure( 
			DEBUG=True, TEMPLATE_DEBUG=True, 
			TEMPLATE_DIRS=(conf['templatePath'])
			)

	if not opts:
		print __doc__
		return 1

	for opt, arg in opts:
		if opt in ("--clear-db"):
			db_conn = sqlite3.connect( conf['db_file'], detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
			db_conn.row_factory = sqlite3.Row
			db_cur = db_conn.cursor()
			db_cur.executescript("""
				DROP TABLE IF EXISTS post;

				CREATE TABLE post(
					id INTEGER PRIMARY KEY,
					title VARCHAR(255),
					url VARCHAR(255),
					body TEXT,
					abstract TEXT,
					cre_date TIMESTAMP,
					sys_upd REAL,
					src VARCHAR(255),
					frontmatter TEXT
				);
				""")
			db_conn.commit()
			print 'A clean db file has been initialized.'

		if opt in ("-g","--generate"):
			myblog = blog(conf)
			myblog.updPosts()
			myblog.updIndex()

		if opt in ("--add-post"):
			myblog = blog(conf)
			myblog.addPost("%s/%s" % (conf['contentDir'], arg))
			myblog.updIndex()

		if opt in ("--update-index"):
			myblog = blog(conf)
			myblog.updIndex()

		if opt in ("--clear-html"):
			path = conf['htmlDir']
			for i in os.listdir(path):
				d = "%s/%s" % (path, i)
				if os.path.isdir(d):
					shutil.rmtree(path=d, ignore_errors=True)
				else:
					os.remove(d)
			print "Deleted all files in %s." % conf['htmlDir']

if __name__ == "__main__": 
	sys.exit(main(*sys.argv))
