import os
import yaml

def conf_locate(cpath = None):
	if cpath and cpath != '.':
		# more testing need to be done here.
		return cpath
	confpath = None
	cwd = os.getcwd()
	h,t = os.path.split(cwd) # head, tail
	
	while h != os.sep:
		if os.path.isdir(
				os.path.join(h,t,'.bucket3')
				):
			confpath = os.path.join(h,t)
			break
		else:
			h,t = os.path.split(h)
	if not confpath:
		print 'bucket3.tools.conf_locate: Unable to locate a bucket3 configuration.'
		return None
	else:
		return confpath

def conf_get(cpath = None):
	cpath = conf_locate(cpath)
	if not cpath:
		print 'bucket3.tools.conf_get: Unable to read bucket3 configuration.'
		return None
	conf_file = os.path.join(cpath, '.bucket3', 'conf.yaml')
	conf = yaml.load(open(conf_file,mode='r').read())
	return conf


def post_new(slug='', ext=None, cpath='.'):
	import pkgutil
	from datetime import datetime
	from dateutil.tz import tzlocal
	
	s = pkgutil.get_data('bucket3', 'conf/post.example.md')
	s = s.replace('_date_time_now_', datetime.now(tzlocal()).strftime('%Y-%m-%d %H:%M:%S %z') )
	s = s.replace('_post_slug_', slug)		
	if not ext:
		c = conf_get(cpath)
		if not c:
			print "bucket3.b3tools.post_new: unable to locate conf.yaml."
			return 1
		if c['default_file_ext']:
			ext = c['default_file_ext']
		else:
			ext = ".md"
			
	prefix = datetime.now().strftime('%y%m%d')
	filename = "%s-%s.%s" % (prefix, slug, ext)
	f = open(filename,'w')
	f.write(s.encode('utf8'))
	f.close()
	print "Created %s." % filename		

def blog_clean(cpath):
	import shutil
	c = conf_get(cpath)
	if not c:
		print 'bucket3.b3tools.blog.clean: Unable to locate conf.yaml.'
		return 1
	
	html_dir = os.path.abspath(c['html_dir'])
	data_dir = os.path.abspath(os.path.join(c['root_dir'], '.bucket3', '_data'))
	
	ok = raw_input('Delete EVERYTHING under \n%s and \n%s \n(y/N)' % ( html_dir,data_dir ) )
	if ok in ('Y','y'):
		for p in [ html_dir, data_dir ]:
			for i in os.listdir(p):
				d = os.path.join( p,i)
				if os.path.isdir(d):
					shutil.rmtree(path=d, ignore_errors=True)
				else:
					os.remove(d)
			print "Deleted all files in %s." % p
	else: 
		print "Canceled."

def blog_new(path):
	import shutil
	import pkgutil
	
	path = os.path.abspath(path) # "normalize" path.
	bucket3_path = os.path.join(path,'.bucket3')
	bucket3_themes_path = os.path.join(bucket3_path,'themes')
	bucket3_posts_path = os.path.join(path,'posts')
	bucket3_html_path = os.path.join(path,'html')
	conf_file = os.path.join(bucket3_path, 'conf.yaml')
	
	if not os.path.isdir(bucket3_path):
		os.mkdir(bucket3_path)
		print "Created %s." % bucket3_path
	
	if not os.path.isfile(conf_file):
		import pkgutil
		s = pkgutil.get_data('bucket3', 'conf/conf.example.yaml')
		s = s.replace('_top_blog_dir_', path)
		s = s.replace('_html_dir_', os.path.join(path, 'html'))
		f = open(conf_file, 'w')
		f.write(s.encode('utf8'))
		f.close()
		print "\nCreated: %s \nMake sure you edit it before moving on!\n" % conf_file
	else:
		print "%s already exists." % conf_file
	
	if not os.path.isdir(bucket3_posts_path):
		os.mkdir(bucket3_posts_path)
		print "Created %s." % bucket3_posts_path
		print "Your posts should be placed there.\n"
	
	if not os.path.isdir(bucket3_html_path):
		os.mkdir(bucket3_html_path)
		print "Created %s." % bucket3_html_path
		print "Rendered HTML pages will go there automatically.\n"
		
	if not os.path.isdir(bucket3_themes_path):
		os.mkdir(bucket3_themes_path)
		print "Created %s." % bucket3_themes_path
		print "Templates, CSS, and javascript files go there."
			
	default_template_dir = os.path.join( os.path.dirname( 
		os.path.abspath( __file__ ) ),
		'_themes', 'bucket3')
	shutil.copytree(default_template_dir, os.path.join(bucket3_themes_path, 'bucket3'))
	print 'Copied default theme (bucket3).\n'

