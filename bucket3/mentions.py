from TwitterSearch import *
import requests
import urllib
from urlparse import urlparse
import yaml
import os
import hashlib
import sqlite3
from webmentiontools.urlinfo import UrlInfo
from webmentiontools.webmentionio import WebmentionIO


class Mentions():
    def __init__(self, conf=(), verbose=1):
        self.verbose = verbose
        self.conf = conf

        self.data_dir = os.path.join(conf['root_dir'], '.bucket3', 'data')
        self.db_conn = sqlite3.connect(os.path.join(self.data_dir, 'posts'))
        self.db_conn.row_factory = sqlite3.Row

        # This is the blog URL without http://
        # and then urlencoded
        self.twitterSearchTerm = urllib.quote(
            ''.join(urlparse(conf['blog']['url'])[1:]),
            '')

        self.readInfoDb()

    def hash(self, txt):
        return hashlib.md5(txt).hexdigest()

    def normalizeUrl(self, url):
        parts = urlparse(url)
        return '%s://%s%s' % (parts.scheme, parts.netloc, parts.path)

    def readInfoDb(self):
        self.status_file = os.path.join(self.conf['mentions_dir'], 'info.yaml')
        if not os.path.isfile(self.status_file):
            self.status = {}
            self.status['twitter'] = {'last_id':0}
            self.status['webmention_io'] = {'last_id':0}
        else:
            f = open(self.status_file, mode='r')
            self.status = yaml.load(f.read())
            f.close()

    def writeInfoDb(self):
        f = open(self.status_file, mode='w')
        f.write(yaml.dump(self.status))
        f.close()

    def readUrlDb(self, url):
        # for every post URL we create a separate YAML file
        # containing all the "mentions".
        url = self.normalizeUrl(url)
        url_hash = self.hash(url)
        path = os.path.join(self.conf['mentions_dir'], '%s.yaml' % url_hash)
        if not os.path.isfile(path):
            data = {
                'url': url,
                'tweets': {},
                'webmention_io': {},
            }
            self.writeUrlDb(data)
            return data
        else:
            f = open(path, mode='r')
            data = yaml.load(f.read())
            if self.verbose > 1:
                print 'Read %s' % path
                print 'data = %s' % data
            if not data.has_key('webmention_io'):
                data['webmention_io'] = {}
            if not data.has_key('tweets'):
                data['tweets'] = {}
            f.close()
            return data

    def writeUrlDb(self, data):
        data['url'] = self.normalizeUrl(data['url'])
        url_hash = self.hash(data['url'])
        path = os.path.join(self.conf['mentions_dir'], '%s.yaml' % url_hash)
        f = open(path, mode='w')
        f.write(yaml.dump(data, encoding=('utf-8')))
        f.close()

    def cacheImage(self, image_url):
        if not image_url:
            return 'default.png'
        
        url_hash = self.hash(image_url)
        ext = os.path.splitext(image_url)[1]
        ext = ext.split('?')[0] # make sure we remove any parameters in the end.

        file_dir = os.path.join(self.conf['mentions_dir'], 'images')
        file_path = os.path.join(self.conf['mentions_dir'], 'images', '%s%s' % (url_hash, ext))
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)
        if os.path.isfile(file_path):
            return '%s%s' % (url_hash, ext)

        req = requests.get(image_url)
        data = req.content
        f = open(file_path, mode='wb')
        f.write(data)
        f.close()

        return '%s%s' % (url_hash, ext)

    def expandUrl(self, url):
        # Helper method to expand short URLs
        try:
            r = requests.head(url)
            if r.status_code in range(200, 300):
                return format(r.url)
            elif r.status_code in range(300, 400):
                # Some servers redirect http://host/path to /path/
                parts1 = urlparse(url)
                parts2 = urlparse(r.headers['location'])
                if parts2.netloc == '':
                    new_url = '%s://%s%s' % (parts1.scheme, parts1.netloc, parts2.path)
                else:
                    new_url = r.headers['location']
                return self.expandUrl(new_url)
            else:
                return format(r.status_code)
        except:
            return 'error'


    def touchBucket3PostByURL(self, url):
        p = self.db_conn.execute('SELECT * FROM posts WHERE url=?', (url,)).fetchone()
        if p:
            path = os.path.join(self.conf['root_dir'], p['src'])
            os.utime(path, None)

    def getTwitterMentions(self):
        try:
            print 'last id = %s' % self.status['twitter']['last_id']

            tso = TwitterSearchOrder()
            tso.setKeywords([self.twitterSearchTerm])
            tso.setCount(100)
            tso.setIncludeEntities(True)
            tso.setResultType('recent')
            if self.status['twitter']['last_id']:
                tso.setSinceID(self.status['twitter']['last_id'])

            ts = TwitterSearch(
                consumer_key=self.conf['twitter_app']['consumer_key'],
                consumer_secret=self.conf['twitter_app']['consumer_secret'],
                access_token=self.conf['twitter_app']['access_token'],
                access_token_secret=self.conf['twitter_app']['access_token_secret']
             )
            i = 1

            # this is where the fun actually starts
            for tweet in ts.searchTweetsIterable(tso):
                print "#%s.  #%s" % ( i , tweet['id'] )
                print '@%s tweeted: %s' % ( tweet['user']['screen_name'], tweet['text'] )
                if self.status['twitter']['last_id'] < tweet['id']:
                    self.status['twitter']['last_id'] = tweet['id']

                for u in tweet['entities']['urls']:
                    x = self.expandUrl(u['expanded_url'])
                    print x
                    data = self.readUrlDb(x)
                    data['tweets'][tweet['id']] = {
                        'id': tweet['id'],
                        'user_screen_name': tweet['user']['screen_name'],
                        'user_name': tweet['user']['name'],
                        'user_id': tweet['user']['id'],
                        'profile_image_url': tweet['user']['profile_image_url'],
                        'profile_image_local': self.cacheImage(tweet['user']['profile_image_url']),
                        'text': tweet['text'],
                        'created_at': tweet['created_at'],
                        }
                    self.writeUrlDb(data)
                    self.touchBucket3PostByURL(x)
                i += 1

        # take care of all those ugly errors if there are some
        except TwitterSearchException as e:
            print(e)

        self.writeInfoDb()

    def getWebMentions(self):
        if 'webmention_io' not in self.conf:
            return False
        wio = WebmentionIO(self.conf['webmention_io']['token'])
        last_id = self.status['webmention_io']['last_id']
        print 'last id = %s' % last_id
        ret = wio.linksToDomain(urlparse(self.conf['blog']['url'])[1]) #domain of blog url
        if not ret:
            print wio.error
            return False

        i = 1
        for mention in ret['links']:
            if mention['id'] > self.status['webmention_io']['last_id']:
                self.status['webmention_io']['last_id'] = mention['id']

                print 
                print '%02d Webmention.io ID: %s' % (i, mention['id'] )
                print '    Source: %s' % mention['source']
                print '    Target: %s' % mention['target']
                print '    Verification Date: %s' % mention['verified_date']

                # Now use UrlInfo to get some more information about the source.
                # Most web apps showing webmentions, will probably do something 
                # like this.
                info = UrlInfo(mention['source'])
                print '    Source URL info:'
                print '        Title: %s' % info.title()
                print '        Pub Date: %s' % info.pubDate()
                print '        in-reply-to: %s' % info.inReplyTo()
                print '        Author image: %s' % info.image()

                x = self.normalizeUrl(mention['target'])
                data = self.readUrlDb(x)
                data['webmention_io'][mention['id']] = {
                    'source': str(mention['source']),
                    'target': str(mention['target']),
                    'verified_date': str(mention['verified_date']),
                    'source_title': str(info.title()),
                    'source_pub_date': str(info.pubDate()),
                    'source_in_reply_to': str(info.inReplyTo()),
                    'source_image': str(info.image()),
                    'source_image_local': self.cacheImage(info.image()),
                    'source_snippet': info.snippetWithLink(mention['target'])
                    }
                self.writeUrlDb(data)
                self.touchBucket3PostByURL(x)
                i += 1
        self.writeInfoDb()


if __name__ == '__main__':
    pass
