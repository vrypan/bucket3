from bucket3.bucket import bucket
from bucket3.handlers.h_markdown import h_markdown 

import markdown
import codecs
import sys,os
import yaml
from datetime import datetime
import time

from django.template import Template, Context, loader
class h_html(h_markdown):
	@classmethod
	def types(cls):
		return ('.html',)
	def toHTML(self, content):
		return content
