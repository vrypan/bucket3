#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import shutil
from datetime import datetime
import time
import calendar
import hashlib
from operator import itemgetter

import yaml
import markdown2
from jinja2 import Template, FileSystemLoader, Environment
import sqlite3
import re
import pickle

class contentFilters():
	exts = ('.md', '.markdown', '.wordpress', '.html')
	
	def toHtml(self, txt, ext='.markdown'):
		if ext=='.markdown' or ext=='.md':
			return self.markdownToHtml(txt)
		elif ext=='.wordpress':
			return self.wordpressToHtml(txt)
		elif ext=='.html':
			return self.html2Html(txt)
		else:
			return txt
	
	def markdownToHtml(self, txt):
		ret = markdown2.markdown(txt)
		return ret
	
	def wordpressToHtml(self,txt):
		txt = re.sub(r'\r\n|\r|\n', '\n', txt.strip()) # normalize newlines
		paras = re.split('\n{2,}', txt)
		paras = ['<p>%s</p>' % p.replace('\n', '<br />') for p in paras]
		txt2 = '\n'.join(paras)
		return txt2.decode('utf-8')
	
	def html2Html(self,txt):
		return txt.decode('utf-8')

class Bucket3():
	
	def __init__(self, conf=(), verbose=1 ):
		self.verbose = verbose

		time.tzset()
		self.filters = contentFilters()
		
		self.root_url = conf['blog']['url']
		self.root_dir = conf['root_dir']
		self.mentions_dir = conf['mentions_dir']
		self.data_dir = os.path.join(self.root_dir, '.bucket3', 'data')
		self.posts_dir = os.path.join(self.root_dir, 'posts')
		self.html_dir = os.path.join(self.root_dir, 'html')

		
		if 'use_slugs' in conf:
			self.use_slugs = conf['use_slugs']
		else:
			self.use_slugs = False
		
		if 'tags_lowercase' in conf:
			self.tags_lowercase = conf['tags_lowercase']
		else:
			self.tags_lowercase = False

		if 'posts_in_homepage' in conf:
			self.posts_in_homepage = conf['posts_in_homepage']
		else:
			self.posts_in_homepage = 10
		
		if not os.path.exists(self.data_dir):
			os.makedirs(self.data_dir)
		
		blog = conf['blog']

		# we will need rss_tags both in templates and program flow,
		# setting both makes it easier.

		if 'rss_tags' in conf and conf['rss_tags']:
			self.rss_tags = conf['rss_tags']
			blog['rss_tags'] = conf['rss_tags']
		else:
			self.rss_tags = False
			blog['rss_tags'] = False
		
		if 'theme' in conf and conf['theme']:
			self.theme = conf['theme']
		else:
			self.theme = 'bucket3'
		
		self.template_dir = [
				os.path.join(self.root_dir, '.bucket3', 'themes', self.theme, 'templates'),
				os.path.join(self.root_dir, '.bucket3', 'themes', 'bucket3', 'templates'),
				os.path.join( os.path.dirname( os.path.abspath( __file__ ) ),
					'_themes', 'bucket3', 'templates'), # last resort, the bucket3 theme downloaded with the app
				]
		
		self.tpl_env = Environment(loader=FileSystemLoader(self.template_dir))
		self.tpl_env.globals['blog'] = blog
		self.tpl_env.globals['_months'] = [calendar.month_name[i] for i in range(0,13)] #yes, needs to start from zero.
		self.tpl_env.globals['_months_short'] = [calendar.month_abbr[i] for i in range(0,13)] #yes, needs to start from zero.
		self.tpl_env.globals['_now'] = datetime.now()
		self.db_conn = sqlite3.connect( os.path.join(self.data_dir, 'posts') )
		self.db_conn.row_factory = sqlite3.Row
		self.render_Q = set()

	def util_rel_path(self, abs_path):
		abs_path = os.path.abspath(abs_path) #make sure path is absolute
		return abs_path[ len(self.root_dir)+1 : ]

	def util_abs_path(self, rel_path):
		return os.path.join(self.root_dir, rel_path)
	
	def util_txt_abstract(self, txt):
		txt = re.sub('<[^<]+?>', '', txt)
	
	def util_parse_frontmatter(self, txt):
		meta = yaml.load(txt)
		meta['title'] = meta['title'].strip()
		if type(meta['date']) != datetime:
			meta['date'] = datetime.strptime(meta['date'][:16], '%Y-%m-%d %H:%M')
		
		if 'tags' in meta and meta['tags']:
			meta['tags'] = [t.strip() for t in meta['tags'].lower().split(',') if t.strip() ]
		else:
			meta['tags'] = []

		if 'attached' in meta and meta['attached']:
			meta['attached'] = [a.strip() for a in meta['attached'].split(',') if a.strip() ]
		else:
			meta['attached'] = []
		
		if self.use_slugs:
			if 'slug' in meta and meta['slug']:
				pass
			else:
				if 'id' in meta and meta['id']:
					meta['slug'] = str(meta['id'])
				else:
					# TODO: a "slugify" method is needed here, but the md5(txt) will do for now.
					meta['slug'] = hashlib.md5(txt).hexdigest()
		else:
			if 'id' in meta and meta['id']:
				meta['slug'] = str(meta['id'])
			else:
				meta['slug'] = hashlib.md5(txt).hexdigest()
		
		meta['fs_path'] = os.path.join(
			self.html_dir,
			str(meta['date'].year),
			str('{:02d}'.format(meta['date'].month)),
			str('{:02d}'.format(meta['date'].day)),
			meta['slug'])
		
		meta['url'] = "%s%s/%s/%s/%s/" % (
			self.root_url,
			str(meta['date'].year),
			str('{:02d}'.format(meta['date'].month)),
			str('{:02d}'.format(meta['date'].day)),
			meta['slug'])
		
		return meta

	def fs_post_get(self, path):
		if self.verbose > 1:
			print "DEBUG: fs_post_get(%s)" % path
		if not os.path.splitext(path)[1] in self.filters.exts:
			return None
		
		abs_path = self.util_abs_path(path)

		post_id = hashlib.sha1(path).hexdigest()
		
		txt = open(abs_path,'r').read()
		(dummy, frontmatter, body) = txt.split('---',2)
		
		if self.verbose > 1:
			print 'Reading %s...' % path
		
		meta = self.util_parse_frontmatter(frontmatter)
		
		body_html = self.filters.toHtml(txt=body, ext=os.path.splitext(path)[1])
		
		# rewrite IMG tags pointing to local images
		body_html = re.sub(
			r" src=[\"']([^/]+?)[\"']", #only for relative links!
			' src="%s%s"' % (meta['url'], r"\1"),
			body_html )
		
		# rewrite links pointing to local files
		body_html = re.sub(
			r" href=[\"']([^/]+?)[\"']", #only for relative links!
			' href="%s%s"' % (meta['url'], r"\1"),
			body_html )
		
		return {
			'id': post_id,
			'title': meta['title'],
			'date': int( meta['date'].strftime("%s") ),
			'src': path,
			'tags': "|%s|" % '|'.join(meta['tags']), # store as "|tag1|tag2|..|tagN|"
			'slug': meta['slug'],
			'meta': pickle.dumps(meta),
			'html':body_html,
			'url': meta['url']
			}

	def fs_post_get_id(self, rel_path):
		path = self.util_abs_path(rel_path)
		if not os.path.splitext(path)[1] in self.filters.exts:
			return None
		post_id = hashlib.sha1(rel_path).hexdigest()
		return post_id

	def db_post_del(self, id):
		if self.verbose:
			print "Deleting post [id:%s]..." % id,
		post = self.db_post_get(id)
		if not post and self.verbose:
			print "Not found. Ignoring."
			return
		self.db_conn.execute('DELETE FROM posts WHERE id=?', (id,) )
		self.rq_post_deps(post)
		if self.verbose:
			print "Done."

	def db_init(self):
		self.db_conn.executescript("""
			CREATE TABLE IF NOT EXISTS posts(
			id TEXT PRIMARY KEY,
			title TEXT,
			date INTEGER,
			src TEXT,
			tags TEXT,
			slug TEXT,
			meta TEXT,
			html TEXT,
			url TEXT
			);
		""")
	
	def db_post_expand(self, row):
		p = dict(zip(row.keys(), row))
		dt = datetime.fromtimestamp(p['date'])
		p['year'] = dt.year
		p['month'] = '{:02d}'.format(dt.month)
		p['day'] = '{:02d}'.format(dt.day)
		p['meta'] = pickle.loads(str(row['meta']))
		return p

	def db_post_get(self, id):
		p = self.db_conn.execute('SELECT * FROM posts WHERE id=?', (id,) ).fetchone()
		if p:
			return self.db_post_expand(p)
		else:
			return None
	
	def db_post_get_all(self, start=0, count=25, order_by="date DESC"):
		if count:
			for p in self.db_conn.execute('SELECT * FROM posts ORDER BY %s LIMIT %s, %s' % (order_by, start, count)).fetchall():
				yield self.db_post_expand(p)
		else:
			for p in self.db_conn.execute('SELECT * FROM posts ORDER BY %s' % (order_by,)).fetchall():
				yield self.db_post_expand(p)
	
	def db_post_get_by_year(self, year):
		min_ts = int( time.mktime( (year,   1,1,0,0,0,0,0,0) ) )
		max_ts = int( time.mktime( (year+1, 1,1,0,0,0,0,0,0) ) )
		for p in self.db_conn.execute('SELECT * FROM posts WHERE date>=? AND date<? ORDER BY date DESC', (min_ts, max_ts) ):
			yield self.db_post_expand(p)

	def db_post_get_counts_by_year(self):
		r = self.db_conn.execute('SELECT MIN(date) as min, MAX(date) as max FROM posts').fetchone()
		if not r:
			return None
		min_year = datetime.fromtimestamp(r['min']).year
		max_year = datetime.fromtimestamp(r['max']).year
		counts = []
		for year in range(min_year, max_year+1):
			for month in range(1,13):
				min_ts = int( time.mktime( (year, month,  1,0,0,0,0,0,0) ) )
				max_ts = int( time.mktime( (year, month+1,1,0,0,0,0,0,0) ) )
				p = self.db_conn.execute('SELECT COUNT(*) as count FROM posts WHERE date>=? AND date<? ORDER BY date DESC', (min_ts, max_ts) ).fetchone()
				counts.append( {"year": year, "month":month, "count":p['count']} )
		return counts

	def db_post_get_by_month(self, year, month):
		min_ts = int( time.mktime( (year, month,  1,0,0,0,0,0,0) ) )
		max_ts = int( time.mktime( (year, month+1,1,0,0,0,0,0,0) ) )
		for p in self.db_conn.execute('SELECT * FROM posts WHERE date>=? AND date<? ORDER BY date DESC', (min_ts, max_ts) ):
			yield self.db_post_expand(p)
	
	def db_post_get_by_tag(self, tag):
		for p in self.db_conn.execute('SELECT * FROM posts WHERE tags like ? ORDER BY date DESC', ('%|'+tag+'|%',) ):
			yield self.db_post_expand(p)

	def db_post_put(self, post):
		db_post = self.db_post_get(post['id'])
		if db_post:
			self.rq_post_deps(db_post)
		
		self.db_conn.execute("""
			REPLACE INTO posts(id, title, date, src, tags, slug, meta, html, url)
			VALUES (?,?,?,?,?,?,?,?,?)
			""",
				(
				post['id'],
				post['title'],
				post['date'],
				post['src'],
				post['tags'],
				post['slug'],
				post['meta'],
				post['html'],
				post['url']
				)
			)
		self.db_conn.commit()
		self.render_Q.update( [('post', post['id']), ] )

		self.rq_post_deps(post)
	
	def rq_post_deps(self, post):
		""" Add actions to the render queue related to a new/modified post."""

		actions = []
		
		post_date = datetime.fromtimestamp(int(post['date']))
		
		
		actions.append( ('archive_year', post_date.year) )
		actions.append( ('archive_month', (post_date.year, post_date.month) ) )
		
		for tag in post['tags'].split('|')[1:-1]:
			tag = tag.strip()
			actions.append( ('tag', tag) )

		actions.append( ('rss',) )
		actions.append( ('sitemap',) )
		actions.append( ('homepage',) )
		actions.append( ('archive_main',) )
		
		self.render_Q.update(actions)
	
	def rq_do(self):
		""" Go through the render queue and do what has to be done. """
		for task in self.render_Q:
			if task[0] == 'post':
				if self.verbose:
					print 'Rendering post    [id:%s]...' % task[1],
				self.render_post(task[1])
				if self.verbose:
					print "Done."
			
			elif task[0] == 'archive_main':
				if self.verbose:
					print "Rendering archive [main]...",
				self.render_archive_main()
				if self.verbose:
					print "Done."

			elif task[0] == 'archive_year':
				if self.verbose:
					print "Rendering archive [year:%s]..." % task[1],
				self.render_archive_year( year=task[1] )
				if self.verbose:
					print "Done."
				
			elif task[0] == 'archive_month':
				if self.verbose:
					print "Rendering archive [year:%s, month:%s]..." % (task[1][0], task[1][1]),
				self.render_archive_month( year=task[1][0], month=task[1][1] )
				if self.verbose:
					print "Done."
			
			elif task[0] == 'tag':
				if self.verbose:
					print "Rendering archive [tag:%s]..." % task[1],
				self.render_archive_tag(task[1])
				if self.verbose:
					print "Done."
			
			elif task[0] == 'rss':
				self.render_rss()
			
			elif task[0] == 'sitemap':
				if self.verbose:
					print "Rendering sitemap.xml... ",
				self.render_xml_sitemap()
				if self.verbose:
					print "Done."
			
			elif task[0] == 'homepage':
				if self.verbose:
					print "Rendering homepage...",
				self.render_home()
				if self.verbose:
					print "Done."
			# MORE HERE!!!

	def render_html_skel(self):
		assets_dir = os.path.join(self.html_dir, '_')
		
		if not os.path.exists(assets_dir):
			os.makedirs(assets_dir)
		
		for x in ['css', 'js', 'img']:
			# create /_/<x> and populate with css files from _assets/<x>
			x_dir = os.path.join(assets_dir, x)
			if self.verbose:
				print "   Populating /_/%s..." % x,
			if not os.path.exists(x_dir):
				os.mkdir(x_dir)
			for f in os.listdir(os.path.join(self.root_dir, '.bucket3', 'themes', self.theme, 'assets', x)):
				shutil.copy2(os.path.join( self.root_dir, '.bucket3', 'themes', self.theme, 'assets', x, f), x_dir)
			if self.verbose:
				print "Done."
		
		if os.path.exists(os.path.join( self.root_dir, '.bucket3', 'themes', self.theme, 'robots.txt')):
			if self.verbose:
				print "   Copying robots.txt...",
			shutil.copy2(
				os.path.join(self.root_dir, '.bucket3', 'themes', self.theme, 'robots.txt'),
				self.html_dir
				)
			if self.verbose:
				print "Done."
		"""
		Look for files under <theme_name>templates/static
		These are files like 404.html, about.html, etc, that should be generated once and placed under /filename.html in our site.
		IMPORTANT: these files are *NOT* inherited from the default template! You have to create or copy them!
		"""
		for static_page in os.listdir( os.path.join(self.root_dir, '.bucket3', 'themes', self.theme, 'templates', 'static') ):
			if self.verbose:
				print "   Rendering static page %s..." % static_page,
			tpl = self.tpl_env.get_template('static/%s' % static_page)
			html = tpl.render()
			f = open(os.path.join(self.html_dir, static_page), 'w')
			f.write(html.encode('utf8'))
			f.close()
			if self.verbose:
				print "Done."

		# Copy cached images (avatars, etc) from mentions/images to html/images
		images_src_dir = os.path.join(self.mentions_dir, 'images')
		images_dst_dir = os.path.join(self.html_dir, 'images')
		if os.path.exists(images_src_dir):
			if not os.path.exists(images_dst_dir):
				os.makedirs(images_dst_dir)
			for img in os.listdir(images_src_dir):
				shutil.copy2(os.path.join(images_src_dir, img), images_dst_dir)
	
	def render_post(self, post_id):
		post = self.db_post_get(post_id)
		mentions = self.mentions_get(post['url'])
		
		tpl = self.tpl_env.get_template('post.html')
		html = tpl.render(meta=post['meta'], body=post['html'], mentions=mentions)
		if not os.path.exists(post['meta']['fs_path']):
			os.makedirs(post['meta']['fs_path'])
		f = open(os.path.join(post['meta']['fs_path'], 'index.html'), 'w')
		f.write(html.encode('utf8'))
		f.close()
		
		if post['meta']['attached']:
			for a in post['meta']['attached']:
				shutil.copy2(os.path.join( os.path.dirname(self.util_abs_path(post['src'])), a), post['meta']['fs_path'])
	
	def render_home(self):
		if self.posts_in_homepage:
			count = self.posts_in_homepage
		else:
			count = 10
		posts = [ p for p in self.db_post_get_all(count=count) ]
		if not posts:
			return
		tpl = self.tpl_env.get_template('home.html')
		html = tpl.render(index=posts)
		f = open(os.path.join(self.html_dir, 'index.html'), 'w')
		f.write(html.encode('utf8'))
		f.close()
	
	def render_xml_sitemap(self):
		posts = [ {'url':p['meta']['url'], 'date':p['meta']['date']} for p in self.db_post_get_all( count=0 ) ]
		if not posts:
			return
		tpl = self.tpl_env.get_template('sitemap.xml')
		html = tpl.render(posts=posts)
		f = open(os.path.join(self.html_dir, 'sitemap.xml'), 'w')
		f.write(html.encode('utf8'))
		f.close()
	
	def render_rss(self):
		print "   rss.xml...",
		posts = [ p for p in self.db_post_get_all(0,25) ]
		if not posts:
			return
		tpl = self.tpl_env.get_template('rss.xml')
		html = tpl.render(posts=posts)
		f = open(os.path.join(self.html_dir, 'rss.xml'), 'w')
		f.write(html.encode('utf8'))
		f.close()
		print "Done."
		
		if not self.rss_tags:
			return
		for tag in self.rss_tags:
			print "   tag/%s/rss.xml..." % tag,
			posts = [p for p in self.db_post_get_by_tag(tag)]
			if posts:
				tpl = self.tpl_env.get_template('rss.xml')
				html = tpl.render(posts=posts, tag=tag)
				file_dir =  os.path.join(self.html_dir, 'tag', tag)
				if not os.path.exists(file_dir):
					os.makedirs(file_dir)
				f = open( os.path.join( file_dir,'rss.xml' ), 'w')
				f.write(html.encode('utf8'))
				f.close()
			print 'Done.'

	def render_archive_main(self):
		counts_by_year_month = self.db_post_get_counts_by_year()
		if counts_by_year_month:
			tpl = self.tpl_env.get_template('main_archive.html')
			html = tpl.render(counts=counts_by_year_month)
			file_dir =  os.path.join(self.html_dir, 'archive')
			if not os.path.exists(file_dir):
				os.makedirs(file_dir)
			f = open(os.path.join(file_dir, 'index.html' ), 'w')
			f.write(html.encode('utf8'))
			f.close()
	
	def render_archive_year(self, year):
		posts = [ p for p in self.db_post_get_by_year(year) ]
		if posts:
			tpl = self.tpl_env.get_template('archive.html')
			html = tpl.render(index=posts)
			file_dir =  os.path.join(self.html_dir, str(year))
			if not os.path.exists(file_dir):
				os.makedirs(file_dir)
			f = open( os.path.join( file_dir,'index.html' ), 'w')
			f.write(html.encode('utf8'))
			f.close()
	
	def render_archive_month(self, year, month):
		posts = [ p for p in self.db_post_get_by_month(year, month) ]
		if posts:
			month_MM = '{:02d}'.format(month)
			tpl = self.tpl_env.get_template('archive.html')
			html = tpl.render(index=posts)
			file_dir = os.path.join(self.html_dir, str(year),  month_MM )
			if not os.path.exists(file_dir):
				os.makedirs(file_dir)
			f = open(os.path.join( file_dir, 'index.html' ), 'w' )
			f.write(html.encode('utf8'))
			f.close()
	
	def render_archive_tag(self, tag):
		posts = [ p for p in self.db_post_get_by_tag(tag) ]
		if posts:
			tpl = self.tpl_env.get_template('archive.html')
			html = tpl.render(index=posts, tag=tag)
			file_dir =  os.path.join(self.html_dir, 'tag', tag)
			if not os.path.exists(file_dir):
				os.makedirs(file_dir)
			f = open( os.path.join( file_dir,'index.html' ), 'w')
			f.write(html.encode('utf8'))
			f.close()
		
	def ___renderArchives(self):
		idx = idx = self.db_post_get_all(0,25)
		
		max_date = idx[0]['_date']
		min_date = idx[-1]['_date']
		
		for year in range(max_date.year, min_date.year-1, -1):
			recs = [ p for p in idx if p['_date'].year==year]
			if recs:
				tpl = self.tpl_env.get_template('archive.html')
				html = tpl.render(index=recs, year=year)
				f = open(os.path.join(self.html_dir, '%s' % year, 'index.html' ), 'w')
				f.write(html.encode('utf8'))
				f.close()
				max_month = recs[0]['_date'].month
				min_month = recs[-1]['_date'].month
				for month in range( max_month, min_month-1, -1):
					mposts = [ p for p in recs if p['_date'].month==month ]
					if mposts:
						html = tpl.render(index=mposts, year=year, month=month)
						f = open(os.path.join(self.html_dir, '%s' % year, str(month), 'index.html' ), 'w')
						f.write(html.encode('utf8'))
						f.close()
		
		if not os.path.exists(os.path.join(self.html_dir, 'archive')):
			os.makedirs(os.path.join(self.html_dir, 'archive'))
		
		matrix = {}
		for year in range(max_date.year, min_date.year-1, -1):
			matrix[year] = {}
			for month in range(1,13):
				recs = [ p for p in idx if p['_date'].year==year and p['_date'].month==month ]
				matrix[year][month] = len(recs)
		
		tpl = self.tpl_env.get_template('main_archive.html')
		html = tpl.render(counts=matrix)
		f = open(os.path.join(self.html_dir, 'archive', 'index.html' ), 'w')
		f.write(html.encode('utf8'))
		f.close()

	def mentions_get(self, url):
		url_hash = hashlib.md5(url).hexdigest()
		path = os.path.join( self.mentions_dir, '%s.yaml' % url_hash )
		if os.path.isfile(path):
			f = open(path,mode='r')
			data = yaml.load(f.read())
			f.close()
			return data
		else:
			return None
	

if __name__ == '__main__':
	pass
