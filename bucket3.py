#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
sys.path.append('./_lib') # external libraries like jinja and markdown2
import shutil
from datetime import datetime
import time
import calendar
from hashlib import md5
from operator import itemgetter
import argparse

import pickle
import yaml
import markdown2
from jinja2 import Template, FileSystemLoader, Environment
import re


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


class blog():
		
	def __init__(self, conf=() ):
		time.tzset()
		self.filters = contentFilters()
		
		self.root_url = conf['blog_url'] 
		self.root_dir = conf['root_dir']
		self.data_dir = os.path.join(self.root_dir, '_data')
		self.posts_dir = os.path.join(self.root_dir, 'posts')
		self.html_dir = conf['html_dir']
		
		if not os.path.exists(self.data_dir):
			os.makedirs(self.data_dir)
			
		self.getState()

		blog = {
			# these variables are available in all templates.
			# can be used like {{ blog.title }}
			'title': conf['blog_title'],
			'url': conf['blog_url'],
			'description': conf['blog_description'],
			'author': conf['blog_author'],
			'copyright': conf['blog_copyright'],
			'google_site_verification': conf['google_site_verification'],
			'google_analytics_id': conf['google_analytics_id'],
			'disqus_shortname': conf['disqus_shortname'],
		}
		
		if 'theme' in conf and conf['theme']:
			self.theme = conf['theme']
		else:
			self.theme = 'bucket3'
		
		self.template_dir = os.path.join(self.root_dir, '_themes', self.theme, 'templates')	
		self.tpl_env = Environment(loader=FileSystemLoader(self.template_dir))
		self.tpl_env.globals['blog'] = blog
		self.tpl_env.globals['_months'] = [calendar.month_name[i] for i in range(0,13)] #yes, needs to start from zero.
		self.tpl_env.globals['_now'] = datetime.now()
	
	def getState(self):
		data = self.getCache('lastrun')
		if not data:
			self.last_run_timestamp = 0
		else: 
			self.last_run_timestamp = data['timestamp']
	
	def getCache(self,cacheName):
		data = None
		fname = os.path.join(self.data_dir, '%s' % cacheName)
		if not os.path.exists(fname):
			return None
		f = open(fname, 'rb')
		data = pickle.load(f)
		f.close()
		return data
		
	def putCache(self, cacheName, data):
		fname = os.path.join(self.data_dir, '%s' % cacheName)
		f = open(fname, 'wb')
		pickle.dump(data, f)
		f.close
		
	def makeHtmlSkel(self):
		assets_dir = os.path.join(self.html_dir, '_')
		
		if not os.path.exists(assets_dir):
			os.makedirs(assets_dir)
		
		for x in ['css', 'js', 'img']:
			# create /_/<x> and populate with css files from _assets/<x>
			x_dir = os.path.join(assets_dir, x)
			if not os.path.exists(x_dir):
				os.mkdir(x_dir)
			for f in os.listdir(os.path.join(self.root_dir, '_themes', self.theme, 'assets', x)):
				shutil.copy2(os.path.join( self.root_dir, '_themes', self.theme, 'assets', x, f), x_dir)
				
		if os.path.exists(os.path.join( self.root_dir, '_themes', self.theme, 'robots.txt')):
			shutil.copy2(
				os.path.join(self.root_dir, '_themes', self.theme, 'robots.txt'),
				self.html_dir
				)
				
		tpl = self.tpl_env.get_template('404.html')
		html = tpl.render()
		f = open(os.path.join(self.html_dir, '404.html'), 'w')
		f.write(html.encode('utf8'))
		f.close()
				
	def textAbstract(self, txt):
		txt = re.sub('<[^<]+?>', '', txt)

	
	def newPosts(self):
		for root, dirs, files in os.walk(self.posts_dir):
			for f in files:
				if os.path.splitext(f)[1] in self.filters.exts:
					path = os.path.join(root,f)
					ts = os.path.getmtime(path)
					if ts > self.last_run_timestamp:
						yield path, ts
	
	def parseFrontmatter(self, txt):
		meta = yaml.load(txt)
		meta['title'] = meta['title'].strip()
		if type(meta['date']) == datetime:
			meta['_date'] = meta['date']
		else:
			meta['_date'] = datetime.strptime(meta['date'][:16], '%Y-%m-%d %H:%M')
		if 'tags' in meta and meta['tags']:
			meta['tags'] = [t.strip() for t in meta['tags'].split(',') ]
		else:
			meta['tags'] = []
		if 'attached' in meta and meta['attached']:
			meta['attached'] = [a.strip() for a in meta['attached'].split(',') if a.strip()]
		else:
			meta['attached'] = []

		if not 'slug' in meta:
			if 'id' in meta and meta['id']:
				meta['slug'] = str(meta['id'])
			else:
				# TODO: a "slugify" method is needed here, but the md5(txt) will do for now.
				meta['slug'] = md5(txt).hexdigest()

		meta['_path'] = os.path.join(
			self.html_dir, 
			str(meta['_date'].year), 
			str(meta['_date'].month), 
			str(meta['_date'].day), 
			meta['slug'])
		meta['_url'] = "%s%s/%s/%s/%s/" % (
			self.root_url, 
			str(meta['_date'].year), 
			str(meta['_date'].month), 
			str(meta['_date'].day), 
			meta['slug'])
		return meta
		
	def renderPost(self, path):
		txt = open(path,'r').read()
		(dummy, frontmatter, body) = txt.split('---',2)
		print path
		meta = self.parseFrontmatter(frontmatter)
		meta['_update'] = datetime.fromtimestamp(os.path.getmtime(path))

		body_html = self.filters.toHtml(txt=body, ext=os.path.splitext(path)[1])
		
		# rewrite IMG tags pointing to local images
		body_html = re.sub(
			r" src=[\"']([^/]+?)[\"']", #only for relative links!
			' src="%s%s"' % (meta['_url'], r"\1"),
			body_html )
			
		# rewrite links pointing to local files
		body_html = re.sub(
			r" href=[\"']([^/]+?)[\"']", #only for relative links!
			' href="%s%s"' % (meta['_url'], r"\1"),
			body_html )
		
		tpl = self.tpl_env.get_template('post.html')
		html = tpl.render(meta=meta, body=body_html)
		if not os.path.exists(meta['_path']):
			os.makedirs(meta['_path'])
		f = open(os.path.join(meta['_path'], 'index.html'), 'w')
		f.write(html.encode('utf8'))
		f.close()
		
		for a in meta['attached']:
			print '->', path
			shutil.copy2(os.path.join( os.path.dirname(path), a), meta['_path'])
			
		return meta, body_html
		
	def renderHome(self):
		data = self.getCache('all_index')
		
		if not data:
			return
		idx = sorted(data, key=itemgetter('date'), reverse=True)[:10]
		
		tpl = self.tpl_env.get_template('home.html')
		html = tpl.render(index=idx)
		f = open(os.path.join(self.html_dir, 'index.html'), 'w')
		f.write(html.encode('utf8'))
		f.close()
		
	def renderRSS(self):
		data = self.getCache('all_index')

		if not data:
			return
		idx = sorted(data, key=itemgetter('date'), reverse=True)[:10]

		tpl = self.tpl_env.get_template('rss.xml')
		html = tpl.render(posts=idx)
		f = open(os.path.join(self.html_dir, 'rss.xml'), 'w')
		f.write(html.encode('utf8'))
		f.close()
		
	def renderArchives(self):
		data = self.getCache('all_index')
		idx = sorted(data, key=itemgetter('date'), reverse=True)
		max_date = idx[0]['date']
		min_date = idx[-1]['date']
		
		counts = []
		
		for year in range(max_date.year, min_date.year-1, -1):
			recs = [ p for p in idx if p['date'].year==year]
			if recs:
				counts.append( (year, len(recs)) )
				tpl = self.tpl_env.get_template('archive.html')
				html = tpl.render(index=recs, year=year)
				f = open(os.path.join(self.html_dir, '%s' % year, 'index.html' ), 'w')
				f.write(html.encode('utf8'))
				f.close()
				max_month = recs[0]['date'].month
				min_month = recs[-1]['date'].month
				for month in range( max_month, min_month-1, -1):
					mposts = [ p for p in recs if p['date'].month==month ]
					if mposts:
						html = tpl.render(index=mposts, year=year, month=month)
						f = open(os.path.join(self.html_dir, '%s' % year, str(month), 'index.html' ), 'w')
						f.write(html.encode('utf8'))
						f.close()
		
		if not os.path.exists(os.path.join(self.html_dir, 'archive')):
			os.makedirs(os.path.join(self.html_dir, 'archive'))
		tpl = self.tpl_env.get_template('main_archive.html')
		html = tpl.render(counts=counts)
		f = open(os.path.join(self.html_dir, 'archive', 'index.html' ), 'w')
		f.write(html.encode('utf8'))
		f.close()

	def renderTags(self):
		counts = []
		for f in os.listdir(self.data_dir):
			if f.startswith('tag_') and f != 'tag_' :
				
				data = self.getCache(f)
				tag_name = f[4:].decode('utf8')
				counts.append((tag_name,len(data)))
				
				idx = sorted(data, key=itemgetter('date'), reverse=True)
				max_year = idx[0]['date'].year
				min_year = idx[-1]['date'].year

				tpl = self.tpl_env.get_template('tag_archive.html')
				html = tpl.render(index=idx, tag_name=tag_name)
				
				if not os.path.exists(os.path.join(self.html_dir, 'tag', tag_name)):
					os.makedirs(os.path.join(self.html_dir, 'tag', tag_name))
				f = open(os.path.join(self.html_dir, 'tag', tag_name, 'index.html' ), 'w')
				f.write(html.encode('utf8'))
				f.close()
		max_count = max([y for x,y in counts ])
		min_count = min([y for x,y in counts ])
		
		min_px = 10
		max_px = 40
		bold_px = 18

		scale = (max_px-min_px)/(max_count-min_count*1.0)
		
		cloud = [(t, x*scale+min_px) for t,x in counts ]

		if not os.path.exists(os.path.join(self.html_dir, 'tag')):
			os.makedirs(os.path.join(self.html_dir, 'tag'))
		tpl = self.tpl_env.get_template('tag_cloud.html')
		html = tpl.render(cloud=cloud, min_px=min_px, max_px=max_px, bold_px=bold_px)
		f = open(os.path.join(self.html_dir, 'tag', 'index.html' ), 'w')
		f.write(html.encode('utf8'))
		f.close()
			

def main(*argv):
	parser = argparse.ArgumentParser(description="usage: bucket3.py [options]", prefix_chars='-+')

	parser.add_argument("-c", "--config",
		dest="conf_file",
		help="configuration file.")

	parser.add_argument('--skel',
		action='store_true',
		dest='skel',
		default=False,
		help="Copy default assets (css, js, img, etc)?")

	parser.add_argument('--clean-all',
		action='store_true',
		dest='clean_all',
		default=False,
		help="Remove all files from _data/ and from html_dir.")

	parser.add_argument('--home',
		action='store_true',
		dest='home',
		default=False,
		help="(re)render the homepage")

	parser.add_argument('--rss',
		action='store_true',
		dest='rss',
		default=False,
		help="(re)render rss.xml")

	parser.add_argument('--archives',
		action='store_true',
		dest='archives',
		default=False,
		help="(re)render yearly and monthly archives.")
		
	parser.add_argument('--tags',
		action='store_true',
		dest='tags',
		default=False,
		help="(re)render tag archives.")

	parser.add_argument('--new-posts',
		action='store_true',
		dest='new_posts',
		default=False,
		help="check for new posts and render them. Also updates data files used by other functions, like archives, RSS and tags, and render the related html files.")


	# --conf
	args = parser.parse_args()
	if not args.conf_file:
		parser.print_help()
		return
	conf = yaml.load(open(args.conf_file,mode='r').read())
	
	# --clean-all
	if args.clean_all:
		ok = raw_input('Delete EVERYTHING under %s and %s \n(y/N)' % (
			os.path.abspath(conf['html_dir']), 
			os.path.abspath(
				os.path.join( conf['root_dir'], '_data') 
			) 
			))
		if ok in ('Y','y'):
			for p in [ os.path.abspath( conf['html_dir'] ), os.path.abspath( os.path.join( conf['root_dir'], '_data') )]:
				for i in os.listdir(p):
					d = os.path.join( p,i)
					if os.path.isdir(d):
						shutil.rmtree(path=d, ignore_errors=True)
					else:
						os.remove(d)
				print "Deleted all files in %s." % p 
			
	b = blog(conf=conf)
	
	# --skel
	if args.skel:
		b.makeHtmlSkel()

	# --new-posts
	if args.new_posts:
		last_ts = 1
		tagidx = {}
		all_index = b.getCache('all_index')
		if not all_index:
			all_index = []

		for p, ts in b.newPosts():
			if ts > last_ts:
				last_ts = ts # last_ts will hold the latest post's timestamp at the end of the loop.
			pmeta, pbody = b.renderPost(p)
			all_index.append( {'date':pmeta['_date'], 'meta':pmeta, 'body':pbody } )
			for tag in pmeta['tags']:
				if not tag in tagidx:
					cache = b.getCache('tag_%s' % tag )
					if cache:
						tagidx[tag]=cache
					else:
						tagidx[tag] = []
				tagidx[tag].append( {'date':pmeta['_date'], 'meta':pmeta, 'body':pbody } )

		for tag in tagidx.keys():
			if tag.strip():
				b.putCache('tag_%s' % tag, tagidx[tag])
				
		if last_ts > 1:
			b.putCache('lastrun', {'timestamp': last_ts})
			b.putCache('all_index', all_index)
			b.renderHome()
			b.renderArchives()
			b.renderTags()
			b.renderRSS()
				
	# --tags
	if args.tags:
		b.renderTags()
		
	# --rss
	if args.rss:
		b.renderRSS()
	
	# --archives
	if args.archives:
		b.renderArchives()
	
if __name__ == '__main__':
	main()
		
