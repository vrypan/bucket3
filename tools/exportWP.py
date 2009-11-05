# -*- coding: utf-8 -*-
# Copyright: 2009 Panayotis Vryonis
# License: GPL
"""
usage: exportWP.py [options]

Given a Wordpress blog, this script will export all posts (and pages)
as markdown files with frontmatter yaml.

This file is part of bucket3 <http://github.com/vrypan/bucket3>

options:
	--dbname=DBNAME		DB name of WP database
	--dbhost=HOST		HOST for WP database (can be 'local')
	--dbuser=DBUSER		USER for WP database
	--dbpass=PASSWORD	DB password for DBUSER
	--wp-prefix=PREFIX	WP tables prefix
	--export-dir=DIR	Directory where the export files will
						be placed
"""
import MySQLdb, os, sys, getopt

def main(*argv):
	try:
		(opts,args) = getopt.getopt(argv[1:], 
				'gi',
				[
					'dbname=', 
					'dbhost=', 
					'dbuser=', 
					'dbpass=', 
					'wp-prefix=', 
					'export-dir=', 
					])
	except getopt.GetoptError, e:
		print e
		print __doc__
		return 1


	dbhost = None
	dbname = None
	dbuser = None
	dbpass = None
	prfx = None
	exp_dir = None

	for opt, arg in opts:
		if opt == '--dbname':
			dbname = arg
		if opt == '--dbhost':
			dbhost = arg
		if opt == '--dbuser':
			dbuser = arg
		if opt == '--dbpass':
			dbpass = arg
		if opt == '--wp-prefix':
			prfx = arg
		if opt == '--export-dir':
			exp_dir = arg

	if not (dbname and dbuser and dbpass and dbhost and prfx and exp_dir):
		print __doc__
		return 1

	conn = MySQLdb.connect (
			host = dbhost,
			user = dbuser,
			passwd = dbpass,
			db = dbname,
			charset = "utf8", use_unicode = True
			)
	
	cursor = conn.cursor( MySQLdb.cursors.DictCursor )
	cursor.execute("""SELECT *, 
			date_format(post_date, '%Y-%m-%d %T') AS d1, 
			date_format(post_date, '%Y%m') as d2, 
			date_format(post_date, '%Y%m%d') as d3 
			FROM """+prfx+"""wp_posts  
			WHERE post_status = 'publish'
			ORDER by ID DESC
			""" )
	result_set = cursor.fetchall()
	
	for row in result_set:
		print row['ID'], row['post_title']
		cursor2 = conn.cursor( MySQLdb.cursors.DictCursor )
		select_posts = """SELECT * 
			FROM """+prfx+"""wp_term_relationships, """+prfx+"""wp_term_taxonomy, """+prfx+"""wp_terms 
			WHERE object_id = %s 
			AND """+prfx+"""wp_term_relationships.term_taxonomy_id="""+prfx+"""wp_term_taxonomy.term_taxonomy_id 
			AND """+prfx+"""wp_term_taxonomy.term_id="""+prfx+"""wp_terms.term_id""" 
		cursor2.execute(select_posts % row['ID'])
		category = ''
		tag = ''
		for t in cursor2.fetchall():
			if t['taxonomy'] == 'category':
				if not category:
					category = t['name']
				else:
					category = '%s, %s' % (category, t['name'])
			if t['taxonomy'] == 'post_tag':
				if not tag:
					tag = t['name']
				else:
					tag = '%s, %s' % (tag, t['name'])
	
		dir = '%s/wp/%s' % ( exp_dir, row['d2'] )
		file = '%s/%s_%s.markdown' % ( dir, row['d3'], row['ID'] )
		if not os.path.exists(dir):
			os.makedirs(dir)
		fh = open(file,'w')
		fh.write('---\n')
		fh.write('title: >\n %s\n' % row['post_title'].encode('utf8') )
		fh.write('date: %s\n' % row['d1'])
		fh.write('type: %s\n' % row['post_type'].encode('utf8') )
		fh.write('category: %s\n' % category.encode('utf8') )
		fh.write('tags: %s\n' % tag.encode('utf8') )
		fh.write('excerpt: >\n  %s\n' % row['post_excerpt'].encode('utf8').replace("\n"," ").replace('\015','') )
		fh.write('---\n')
		fh.write(row['post_content'].encode('utf8') )
		fh.close()
	
if __name__ == "__main__": 
	sys.exit(main(*sys.argv))
