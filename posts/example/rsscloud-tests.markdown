---
title: testing rssCloud
author: Panayotis Vryonis
date: 2009-11-16 15:32:00 GMT+2
tags: howto
slug: testing-rsscloud
---
I'm interested to see how I could add [rssCloud](http://rsscloud.org/walkthrough.html) support to bucket3.

Here is some code in python that seems to work and notify Dave Winer's cloud server.

	import httplib, urllib
	params = urllib.urlencode({'url': "http://bucket3.com/blog/feed/rss2.xml"})
	headers = {"Content-type": "application/x-www-form-urlencoded", 
		"Accept": "text/plain"}
	conn = httplib.HTTPConnection("rpc.rsscloud.org:5337")
	conn.request("POST", "/rsscloud/ping", params, headers)
	response = conn.getresponse()
	print response.status, response.reason
	data = response.read()
	print data
	conn.close()
