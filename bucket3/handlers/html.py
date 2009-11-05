from bucket3.bucket import bucket
from bucket3.handlers.markdown import markdown

import markdown2
import codecs
import sys,os
import yaml
from datetime import datetime
import time

from django.template import Template, Context, loader
class html(markdown):
	@classmethod
	def types(cls):
		return ('.html',)
	def toHTML(cls, content):
		return content
