#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import shutil
from distutils.dir_util import copy_tree
from datetime import datetime
import time
import calendar
import hashlib
from operator import itemgetter

import yaml
import markdown
from jinja2 import Template, FileSystemLoader, Environment
import sqlite3
import re
import pickle
import unidecode
from htmlmin import minify
from lxml import etree as ET
from copy import deepcopy

class contentFilters():
    exts = ('.md', '.markdown', '.wordpress', '.html')
    def __init__(self, markdown_extensions=[]):
        self.markdown_extensions = markdown_extensions

    def toHtml(self, txt, ext='.markdown'):
        if ext == '.markdown' or ext == '.md':
            return self.markdownToHtml(txt)
        elif ext == '.wordpress':
            return self.wordpressToHtml(txt)
        elif ext == '.html':
            return self.html2Html(txt)
        else:
            return txt

    def markdownToHtml(self, txt):
        ret = markdown.markdown(txt, extensions=self.markdown_extensions, output_format='xhtml5')
        return ret

    def wordpressToHtml(self, txt):
        txt = re.sub(r'\r\n|\r|\n', '\n', txt.strip())  # normalize newlines
        paras = re.split('\n{2,}', txt)
        paras = ['<p>%s</p>' % p.replace('\n', '<br />') for p in paras]
        txt2 = '\n'.join(paras)
        return txt2

    def html2Html(self, txt):
        return txt

def fb_instant_articles_markup(html, url=''):
    html = "<div>" + html +"</div>"
    root = ET.fromstring(html)
    for e in root.iterfind('.//center'):
        if e.text.replace(' ','') == '***':
            e.text = ''
    ET.strip_tags(root, 'center')

    for e in root.findall('.//img'):
        parent_e = next(e.iterancestors())
        if parent_e.tag != 'figure':
            tmp_e = ET.Element('figure')
            tmp_e.append(deepcopy(e))
            parent_e.replace(e, tmp_e)
        
    for h in root.findall('.//h2'):
        h.tag='h1'
    for h in root.findall('.//h3'):
        h.tag='h2'
    
    for e in root.findall('.//p'):
        elements = [el for el in e]
        if len(elements)==1 and elements[0].tail==None and e.text==None:
            tmp_e = deepcopy(elements[0])    
            parent_e = e.getparent()
            parent_e.replace(e, tmp_e)    
        if len(e) == 0 and e.text.strip() == '' and e.tail.strip()=='':
            e.getparent().remove(e)

        for e in root.findall('./pre/code'):
            parent_e = e.getparent()
            tmp_e = ET.Element('blockquote')
            tmp_a = ET.Element('a')
            tmp_a.attrib['href']=url
            tmp_a.text = """
            Visit the original post on my blog to get the code that was displayed here.
            """
            tmp_a.tail=' (Code removed due to limitations of Facebook instant articles.)'
            tmp_e.append(tmp_a)
            parent_e.replace(e, tmp_e)

    ret = ET.tostring(root)
    return ret

def jinja_filter_gravatar(email, size=100, rating='g', default='retro', force_default=False,
    force_lower=False, use_ssl=False):
    # source: https://gist.github.com/Alquimista/3499097
    if use_ssl:
        url = "https://secure.gravatar.com/avatar/"
    else:
        url = "http://www.gravatar.com/avatar/"
    if force_lower:
        email = email.lower()
    hashemail = hashlib.md5(email).hexdigest()
    link = "{url}{hashemail}?s={size}&d={default}&r={rating}".format(
        url=url, hashemail=hashemail, size=size,
        default=default, rating=rating)
    if force_default:
        link = link + "&f=y"
    return link

class Bucket3():

    def __init__(self, conf=(), verbose=1):
        self.verbose = verbose

        time.tzset()

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

        if 'markdown_extensions' in conf:
            self.markdown_extensions = conf['markdown_extensions']
        else:
            self.markdown_extensions = []
        self.filters = contentFilters(markdown_extensions=self.markdown_extensions)

        blog = conf['blog']

        # we will need rss_tags both in templates and program flow,
        # setting both makes it easier.

        if 'posts_prefix' in conf:
                self.posts_prefix = conf['posts_prefix']
                
        if 'rss_tags' in conf and conf['rss_tags']:
            self.rss_tags = conf['rss_tags']
            blog['rss_tags'] = conf['rss_tags']
        else:
            self.rss_tags = False
            blog['rss_tags'] = False

        if 'minify_html' in conf:
            self.minify_html = conf['minify_html']
        else:
            self.minify_html = False

        self.template_dir = [ os.path.join(self.root_dir, 'templates'), ]

        self.tpl_env = Environment(loader=FileSystemLoader(self.template_dir))
        self.tpl_env.filters['gravatar'] = jinja_filter_gravatar
        self.tpl_env.filters['fbia'] = fb_instant_articles_markup
        self.tpl_env.globals['blog'] = blog
        self.tpl_env.globals['_months'] = [calendar.month_name[i] for i in range(0, 13)]  # yes, needs to start from zero.
        self.tpl_env.globals['_months_short'] = [calendar.month_abbr[i] for i in range(0, 13)]  # yes, needs to start from zero.
        self.tpl_env.globals['_now'] = datetime.now()
        self.db_conn = sqlite3.connect(os.path.join(self.data_dir, 'posts'))
        self.db_conn.row_factory = sqlite3.Row
        self.render_Q = set()

        # regexp to extract links from html. Compile once, here.
        regexp_link = r'<a.*(?=href=\"([^\"]*)\")[^>]*>[^<]*</a>'
        self.re_link_extract = re.compile(regexp_link)

    def util_rel_path(self, abs_path):
        abs_path = os.path.abspath(abs_path)  # make sure path is absolute
        return abs_path[len(self.root_dir) + 1:]

    def util_abs_path(self, *rel_path):
        return os.path.join(self.root_dir, *rel_path)

    def util_txt_abstract(self, txt):
        txt = re.sub('<[^<]+?>', '', txt)

    def util_extract_links(self, html):
        links = re.findall(self.re_link_extract, html)
        return links

    def util_slugify(self, str):
        # Credit: http://stackoverflow.com/a/8366771
        str = unidecode.unidecode(str.strip()).lower()
        return re.sub(r'\W+','-',str)

    def util_write_html(self, file_dir, file_content, file_name='index.html'):
        if self.minify_html:
            file_content = minify(file_content, remove_comments=True, remove_empty_space=False)
        if not os.path.exists(file_dir):
                os.makedirs(file_dir)
        f = open(os.path.join(file_dir, file_name), 'w')
        f.write(file_content)
        f.close()

    def util_parse_frontmatter(self, txt):
        meta = yaml.load(txt, Loader=yaml.FullLoader)
        meta['title'] = meta['title'].strip()
        if type(meta['date']) != datetime:
            meta['date'] = datetime.strptime(meta['date'][:16], '%Y-%m-%d %H:%M')

        if 'tags' in meta and meta['tags']:
            meta['tags'] = [t.strip() for t in meta['tags'].lower().split(',') if t.strip()]
        else:
            meta['tags'] = []

        if 'attached' in meta and meta['attached']:
            meta['attached'] = [a.strip() for a in meta['attached'].split(',') if a.strip()]
        else:
            meta['attached'] = []

        if self.use_slugs:
            if 'slug' in meta and meta['slug']:
                pass
            else:
                if 'id' in meta and meta['id']:
                    meta['slug'] = str(meta['id'])
                else:
                    meta['slug'] = self.util_slugify(meta['title'])
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
            print("DEBUG: fs_post_get(%s)" % path)
        if not os.path.splitext(path)[1] in self.filters.exts:
            return None

        abs_path = self.util_abs_path(path)

        post_id = hashlib.sha1(path.encode('utf-8')).hexdigest()

        txt = open(abs_path, 'r').read()
        (dummy, frontmatter, body) = txt.split('---', 2)

        if self.verbose > 1:
            print('Reading %s...' % path)

        meta = self.util_parse_frontmatter(frontmatter)

        body_html = self.filters.toHtml(txt=body, ext=os.path.splitext(path)[1])

        # rewrite IMG tags pointing to local images
        body_html = re.sub(
            r" src=[\"']([^/]+?)[\"']",  # only for relative links!
            ' src="%s%s"' % (meta['url'], r"\1"),
            body_html)

        # rewrite links pointing to local files
        body_html = re.sub(
            r" href=[\"']([^/]+?)[\"']",  # only for relative links!
            ' href="%s%s"' % (meta['url'], r"\1"),
            body_html)

        return {
            'id': post_id,
            'title': meta['title'],
            'date': int(meta['date'].strftime("%s")),
            'src': path,
            # tags store as "|tag1|tag2|..|tagN|"
            'tags': "|%s|" % '|'.join(meta['tags']),
            'slug': meta['slug'],
            'meta': pickle.dumps(meta),
            'html': body_html,
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
            print("Deleting post [id:%s]..." % id, end='')
        post = self.db_post_get(id)
        if not post and self.verbose:
            print("Not found. Ignoring.")
            return
        self.db_conn.execute('DELETE FROM posts WHERE id=?', (id,))
        self.rq_post_deps(post)
        if self.verbose:
            print("Done.")

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
        p['meta'] = pickle.loads(row['meta'])
        return p

    def db_post_get(self, id):
        p = self.db_conn.execute('SELECT * FROM posts WHERE id=?', (id,)).fetchone()
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
        min_ts = int(time.mktime((year, 1, 1, 0, 0, 0, 0, 0, 0)))
        max_ts = int(time.mktime((year + 1, 1, 1, 0, 0, 0, 0, 0, 0)))
        for p in self.db_conn.execute('SELECT * FROM posts WHERE date>=? AND date<? ORDER BY date DESC', (min_ts, max_ts)):
            yield self.db_post_expand(p)

    def db_post_get_counts_by_year(self):
        r = self.db_conn.execute('SELECT MIN(date) as min, MAX(date) as max FROM posts').fetchone()
        if not r:
            return None
        min_year = datetime.fromtimestamp(r['min']).year
        max_year = datetime.fromtimestamp(r['max']).year
        counts = []
        for year in range(min_year, max_year + 1):
            for month in range(1, 13):
                min_ts = int(time.mktime((year, month, 1, 0, 0, 0, 0, 0, 0)))
                max_ts = int(time.mktime((year, month + 1, 1, 0, 0, 0, 0, 0, 0)))
                p = self.db_conn.execute('SELECT COUNT(*) as count FROM posts WHERE date>=? AND date<? ORDER BY date DESC', (min_ts, max_ts)).fetchone()
                counts.append({"year": year, "month":month, "count":p['count']})
        return counts

    def db_post_get_by_month(self, year, month):
        min_ts = int(time.mktime((year, month, 1, 0, 0, 0, 0, 0, 0)))
        max_ts = int(time.mktime((year, month + 1, 1, 0, 0, 0, 0, 0, 0)))
        for p in self.db_conn.execute('SELECT * FROM posts WHERE date>=? AND date<? ORDER BY date DESC', (min_ts, max_ts)):
            yield self.db_post_expand(p)

    def db_post_get_by_tag(self, tag):
        for p in self.db_conn.execute('SELECT * FROM posts WHERE tags like ? ORDER BY date DESC', ('%|'+tag+'|%',)):
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
        self.render_Q.update([('post', post['id']), ])

        self.rq_post_deps(post)

    def rq_post_deps(self, post):
        """ Add actions to the render queue related to a new/modified post."""

        actions = []

        post_date = datetime.fromtimestamp(int(post['date']))

        actions.append(('archive_year', post_date.year))
        actions.append(('archive_month', (post_date.year, post_date.month)))

        for tag in post['tags'].split('|')[1:-1]:
            tag = tag.strip()
            actions.append(('tag', tag))

        actions.append(('rss',))
        actions.append(('sitemap',))
        actions.append(('homepage',))
        actions.append(('archive_main',))

        self.render_Q.update(actions)

    def rq_do(self):
        """ Go through the render queue and do what has to be done. """
        for task in self.render_Q:
            if task[0] == 'post':
                if self.verbose:
                    print('Rendering post    [id:%s]...' % task[1], end='')
                self.render_post(task[1])
                if self.verbose:
                    print("Done.")

            elif task[0] == 'archive_main':
                if self.verbose:
                    print("Rendering archive [main]...", end='')
                self.render_archive_main()
                if self.verbose:
                    print("Done.")

            elif task[0] == 'archive_year':
                if self.verbose:
                    print("Rendering archive [year:%s]..." % task[1], end='')
                self.render_archive_year(year=task[1])
                if self.verbose:
                    print("Done.")

            elif task[0] == 'archive_month':
                if self.verbose:
                    print("Rendering archive [year:%s, month:%s]..." % (task[1][0], task[1][1]), end='')
                self.render_archive_month(year=task[1][0], month=task[1][1])
                if self.verbose:
                    print("Done.")

            elif task[0] == 'tag':
                if self.verbose:
                    print("Rendering archive [tag:%s]..." % task[1], end='')
                self.render_archive_tag(task[1])
                if self.verbose:
                    print("Done.")

            elif task[0] == 'rss':
                self.render_rss()

            elif task[0] == 'sitemap':
                if self.verbose:
                    print("Rendering sitemap.xml... ", end='')
                self.render_xml_sitemap()
                if self.verbose:
                    print("Done.")

            elif task[0] == 'homepage':
                if self.verbose:
                    print("Rendering homepage...", end='')
                self.render_home()
                if self.verbose:
                    print("Done.")
            # MORE HERE!!!

    def render_static_pages(self):
        """
        "static" pages are pages that are not blog posts. Their URL is /<page>.html and not YYYY/MM/DD/.../index.html
        Also, they are not included in the RSS feed, in the archive pages, etc.
        You would usually use a static page for something like about.html, contact.html, 404.html etc.

        They are actual jinja2 templates. They look something like this (this is a 404.html page):

        {% extends "base.html" %}
        {% block page_meta %}
        <meta name="title" content="{{ blog.title }} | Error 404 Page Not Found">
        <meta name="description" content="Error 404: Page not found.">
        {% endblock page_meta %}


        {% block content %}
        <h3 class="entry-title">Error 404: page not found.</h3>
                <p>The page you requested was not found. </p>
        {% endblock %}

        """
        print('Rendering static pages (under skel/). ', end='')
        static_root_src = os.path.join(self.root_dir, 'skel')
        static_root_dst = self.html_dir

        if os.path.exists(static_root_src):
            for path, subdirs, files in os.walk(static_root_src):
                for fname in files:
                    rel_path = os.path.relpath(path, static_root_src)
                    dst_path = os.path.join(static_root_dst, rel_path)
                    ext = os.path.splitext(fname)[1]
                    
                    if not os.path.exists(dst_path):
                        os.makedirs(dst_path)
                    sys.stdout.write('.')
                    if ext in ('.html', '.htm'):
                        html_src = open(os.path.join(path, fname), 'r').read()
                        html = self.tpl_env.from_string(html_src).render()

                        f = open(os.path.join(dst_path, fname), 'w')
                        f.write(html)
                        f.close()
                    else:
                        shutil.copy2(os.path.join(path, fname), dst_path)
        print("Done.")


    def render_post(self, post_id):
        post = self.db_post_get(post_id)
        mentions = self.mentions_get(post['url'])

        tpl = self.tpl_env.get_template('post.html')
        html = tpl.render(meta=post['meta'], body=post['html'], mentions=mentions)
        
        self.util_write_html(post['meta']['fs_path'],html)
        
        if post['meta']['attached']:
            for a in post['meta']['attached']:
                shutil.copy2(os.path.join(os.path.dirname(self.util_abs_path(post['src'])), a), post['meta']['fs_path'])

    def render_home(self):
        if self.posts_in_homepage:
            count = self.posts_in_homepage
        else:
            count = 10
        posts = [p for p in self.db_post_get_all(count=count)]
        if not posts:
            return
        tpl = self.tpl_env.get_template('home.html')
        html = tpl.render(index=posts)
        self.util_write_html(self.html_dir,html)

    def render_xml_sitemap(self):
        posts = [{'url':p['meta']['url'], 'date':p['meta']['date']} for p in self.db_post_get_all( count=0 )]
        if not posts:
            return
        tpl = self.tpl_env.get_template('sitemap.xml')
        html = tpl.render(posts=posts)
        f = open(os.path.join(self.html_dir, 'sitemap.xml'), 'w')
        f.write(html)
        f.close()

    def render_rss(self):
        self.render_rss_core('rss.xml')
        self.render_rss_core('rss-medium.xml')
        self.render_rss_core('rss-fb.xml')
        self.render_rss_tags()
        return

    def render_rss_core(self, template_file='rss.xml'):
        print("   " + template_file +"...", end='')
        posts = [p for p in self.db_post_get_all(0, 25)]
        if not posts:
            return
        tpl = self.tpl_env.get_template(template_file)
        html = tpl.render(posts=posts)
        f = open(os.path.join(self.html_dir, template_file), 'w')
        f.write(html)
        f.close()
        print("Done.")

    def render_rss_tags(self):
        if not self.rss_tags:
            return
        for tag in self.rss_tags:
            print("   tag/%s/rss.xml..." % tag, end='')
            posts = [p for p in self.db_post_get_by_tag(tag)]
            if posts:
                tpl = self.tpl_env.get_template('rss.xml')
                html = tpl.render(posts=posts, tag=tag)
                file_dir = os.path.join(self.html_dir, 'tag', tag)
                if not os.path.exists(file_dir):
                    os.makedirs(file_dir)
                f = open(os.path.join(file_dir, 'rss.xml'), 'w')
                f.write(html)
                f.close()
            print('Done.')


    def render_archive_main(self):
        posts = [p for p in self.db_post_get_all(count=None)]
        if posts:
            tpl = self.tpl_env.get_template('archive.html')
            html = tpl.render(index=posts)
            file_dir = os.path.join(self.html_dir, 'archive')
            self.util_write_html(file_dir, html)
            
    def render_archive_year(self, year):
        posts = [p for p in self.db_post_get_by_year(year)]
        if posts:
            tpl = self.tpl_env.get_template('archive.html')
            html = tpl.render(index=posts)
            file_dir = os.path.join(self.html_dir, str(year))
            self.util_write_html(file_dir, html)
            
    def render_archive_month(self, year, month):
        posts = [p for p in self.db_post_get_by_month(year, month)]
        if posts:
            month_MM = '{:02d}'.format(month)
            tpl = self.tpl_env.get_template('archive.html')
            html = tpl.render(index=posts)
            file_dir = os.path.join(self.html_dir, str(year), month_MM)
            self.util_write_html(file_dir, html)

    def render_archive_tag(self, tag):
        posts = [p for p in self.db_post_get_by_tag(tag)]
        if posts:
            tpl = self.tpl_env.get_template('archive.html')
            html = tpl.render(index=posts, tag=tag)
            file_dir = os.path.join(self.html_dir, 'tag', tag)
            self.util_write_html(file_dir, html)

    def mentions_get(self, url):
        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
        path = os.path.join(self.mentions_dir, '%s.yaml' % url_hash)
        if os.path.isfile(path):
            f = open(path, mode='r')
            data = yaml.load(f.read())
            f.close()
            return data
        else:
            return None
if __name__ == '__main__':
    pass
