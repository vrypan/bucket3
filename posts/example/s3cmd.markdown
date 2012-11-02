---
title: syncing local and remote S3 bucket with s3cmd
author: Panayotis Vryonis
date: 2012-02-11 15:45:00 GMT+2
tags: howto, sync, s3
slug: sync-with-s3cmd
---
So, I started hosting www.bucket3.com to S3.

I use [s3cmd](http://s3tools.org/s3cmd) to upload my files to S3 and keep local and remote files in sync.

I initially uploaded my files using

	s3cmd put --recursive -P html/ s3://www.bucket3.com/

(-P indicates that the uploaded files should be world readable)

Then, whenever I create new content, I use 

	s3cmd sync -P html/ s3://www.bucket3.com/

s3cmd is written in python.
