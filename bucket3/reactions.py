from TwitterSearch import *
import requests

class Reactions():

    def expandUrl(self, url):
        # Helper method to expand short URLs
    	r= requests.head(url)
    	if r.status_code in range (200,300):
    		return format(r.url)
    	elif r.status_code in range (300,400):
    		return self.expandUrl(r.headers['location'])
    	else:
    		return format(r.status_code)

    def getTwitterReactions(self,domain):
        try:
            tso = TwitterSearchOrder()
            tso.setKeywords([domain]) 
            tso.setCount(100)
            tso.setIncludeEntities(True)
            tso.setResultType('recent')

            ts = TwitterSearch(
                consumer_key = '9T1pF31KVGF9f3GY1xSC2w',
                consumer_secret = '4lVdYjpBAeVHba232lnhwnRILpFkk9qLoIfXp1t7X0',
                access_token = '74233-1TdJ3EQfRo1643zW8aMZIGarDFmw0mgHcHH5tEaxgQ',
                access_token_secret = '26quJVgdITg1513AZAC5Wzso6EXhPMXGyTsG39b0mA'
             )
            i = 1
            for tweet in ts.searchTweetsIterable(tso): # this is where the fun actually starts :
                print "#%s.  " % i ,	
                for u in tweet['entities']['urls']:
                    print self.expandUrl(u['expanded_url'])
                print '@%s tweeted: %s' % ( tweet['user']['screen_name'], tweet['text'] )
                i += 1

        except TwitterSearchException as e: # take care of all those ugly errors if there are some
            print(e)

if __name__ == '__main__':
    R = Reactions()
    R.getTwitterReactions('blog.vrypan.net')