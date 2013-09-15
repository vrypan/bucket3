from TwitterSearch import *
import requests
import urllib
from urlparse import urlparse
import yaml
import os
import hashlib
import sqlite3

class Reactions():
    def __init__(self, conf=(), verbose=1 ):
        self.verbose = verbose
        self.conf = conf

        self.data_dir = os.path.join(conf['root_dir'], '.bucket3', 'data')
        self.db_conn = sqlite3.connect( os.path.join(self.data_dir, 'posts') )
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
        self.status_file = os.path.join(self.conf['reactions_dir'], 'info.yaml')
        if not os.path.isfile(self.status_file):
            self.status = {}
            self.status['twitter'] = {'last_id':0}
        else:
            f = open(self.status_file,mode='r')
            self.status = yaml.load(f.read())
            f.close()

    def writeInfoDb(self):
        f = open(self.status_file,mode='w')
        f.write(yaml.dump(self.status))
        f.close()

    def readUrlDb(self, url):
        # for every post URL we create a separate YAML file
        # containing all the "reactions".
        url = self.normalizeUrl(url)
        url_hash = self.hash(url)
        path = os.path.join( self.conf['reactions_dir'], '%s.yaml' % url_hash )
        if not os.path.isfile(path):
            data = {
                'url' : url,
                'tweets': {},
            }
            self.writeUrlDb(data)
            return data
        else:
            f = open(path,mode='r')
            data = yaml.load(f.read())
            f.close()        
            return data

    def writeUrlDb(self, data):
        data['url'] = self.normalizeUrl(data['url'])
        url_hash = self.hash(data['url'])
        path = os.path.join( self.conf['reactions_dir'], '%s.yaml' % url_hash )
        f = open(path,mode='w')
        f.write(yaml.dump(data, encoding=('utf-8')) )
        f.close()

    def cacheImage(self, image_url):
        url_hash = self.hash(image_url)
        ext = os.path.splitext(image_url)[1]

        file_dir = os.path.join( self.conf['reactions_dir'], 'images' )
        file_path = os.path.join( self.conf['reactions_dir'], 'images', '%s%s' % (url_hash, ext) )
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)
        if os.path.isfile(file_path):
            return '%s%s' % (url_hash, ext)

        req = requests.get(image_url)
        data = req.content
        f = open(file_path,mode='wb')
        f.write(data)
        f.close()

        return '%s%s' % (url_hash, ext)
        
    def expandUrl(self, url):
        # Helper method to expand short URLs
    	r= requests.head(url)
    	if r.status_code in range (200,300):
    		return format(r.url)
    	elif r.status_code in range (300,400):
    		return self.expandUrl(r.headers['location'])
    	else:
    		return format(r.status_code)

    def touchBucket3PostByURL(self, url):
        p = self.db_conn.execute('SELECT * FROM posts WHERE url=?', (url,) ).fetchone()
        if p:
            path = os.path.join(self.conf['root_dir'], p['src'])
            os.utime(path, None)

    def getTwitterReactions(self):
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
                consumer_key = self.conf['twitter_app']['consumer_key'] ,
                consumer_secret = self.conf['twitter_app']['consumer_secret'] ,
                access_token = self.conf['twitter_app']['access_token'] ,
                access_token_secret = self.conf['twitter_app']['access_token_secret']
             )
            i = 1
            for tweet in ts.searchTweetsIterable(tso): # this is where the fun actually starts :
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

        except TwitterSearchException as e: # take care of all those ugly errors if there are some
            print(e)

        self.writeInfoDb()
        


if __name__ == '__main__':
    pass