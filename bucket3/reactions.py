from TwitterSearch import *
import requests
import urllib
from urlparse import urlparse
import yaml
import os
import hashlib

class Reactions():
    def __init__(self, conf=(), verbose=1 ):
        self.verbose = verbose
        self.conf = conf

        # This is the blog URL without http://
        # and then urlencoded
        self.twitterSearchTerm = urllib.quote(
            ''.join(urlparse(conf['blog']['url'])[1:]),
            '')

        self.readInfoDb()

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

        url_hash = hashlib.md5(url).hexdigest()

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
        url_hash = hashlib.md5(data['url']).hexdigest()
        path = os.path.join( self.conf['reactions_dir'], '%s.yaml' % url_hash )
        f = open(path,mode='w')
        f.write(yaml.dump(data, encoding=('utf-8')) )
        f.close()
        
    def expandUrl(self, url):
        # Helper method to expand short URLs
    	r= requests.head(url)
    	if r.status_code in range (200,300):
    		return format(r.url)
    	elif r.status_code in range (300,400):
    		return self.expandUrl(r.headers['location'])
    	else:
    		return format(r.status_code)

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
                consumer_key = '9T1pF31KVGF9f3GY1xSC2w',
                consumer_secret = '4lVdYjpBAeVHba232lnhwnRILpFkk9qLoIfXp1t7X0',
                access_token = '74233-1TdJ3EQfRo1643zW8aMZIGarDFmw0mgHcHH5tEaxgQ',
                access_token_secret = '26quJVgdITg1513AZAC5Wzso6EXhPMXGyTsG39b0mA'
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
                        'user_name': tweet['user']['screen_name'],
                        'user_id': tweet['user']['id'],
                        'profile_image_url': tweet['user']['profile_image_url'],
                        'text': tweet['text'],
                        'created_at': tweet['created_at'],
                        }
                    self.writeUrlDb(data)
                i += 1



        except TwitterSearchException as e: # take care of all those ugly errors if there are some
            print(e)

        self.writeInfoDb()
        


if __name__ == '__main__':
    demo_conf = {
        'blog': { 'url': 'http://blog.vrypan.net'},
        'reactions_dir' : './reactions'
    }
    R = Reactions(conf=demo_conf)
    R.getTwitterReactions()