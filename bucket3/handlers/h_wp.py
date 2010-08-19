from bucket3.bucket import bucket
from bucket3.handlers.markdown import markdown
import re

class wp(markdown):
	""" This handler is intended to parse the contents of exportWP.py
	i.e. the HTML code storred in wordpress database.
	"""
	@classmethod
	def types(cls):
		return ('.wordpress','.wp')

	def linebreaks(self, value, autoescape=False):
		"""Converts newlines into <p> and <br />s."""
		"""Code copied from http://code.djangoproject.com/browser/django/trunk/django/utils/html.py """
		value = re.sub(r'\r\n|\r|\n', '\n', value.strip()) # normalize newlines
		paras = re.split('\n{2,}', value)
		if autoescape:
			paras = [u'<p>%s</p>' % escape(p).replace('\n', '<br />') for p in paras]
		else:
			paras = [u'<p>%s</p>' % p.replace('\n', '<br />') for p in paras]
		return u'\n'.join(paras)

	def toHTML(self, content):
		return markdown.toHTML(self, self.linebreaks(content))
