---
title: bucket3 content handlers
author: Panayotis Vryonis
date: 2009-10-30 10:30
tags: documentation,bucket3,handlers
---

You can create your own content handlers, without divinig into bucket3
complexities. The handlers that come by default are:

- **b3_markdown** handles .markdown files.
- **b3_html** handles .html files
- **b3_image** handles images. (It will create a post from a single image)

### Enabling new handlers

Edit bucket3/blog.py and add your own, after

	from bucket3.handlers.markdown import b3_markdown
	from bucket3.handlers.html import b3_html
	from bucket3.handlers.image import b3_image

	post.regHandler(b3_markdown)
	post.regHandler(b3_html)
	post.regHandler(b3_image)


