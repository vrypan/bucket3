
class bucket():
	def __init__(self, conf):
		self.conf = conf
		return self

	def osItemName(self, file):
		return file.split('/')[-1].rpartition('.')[0]

	def osItemDir(self, file, cre_dat, isPage=False):
		if isPage:
			# blog "pages" have "special" handling, and their URLs do not include the date.
			dir = "%s/%s" % ( self.conf['htmlDir'], self.osItemName(file) )
		else:
			dir = "%s/%s/%s" % ( self.conf['htmlDir'], cre_dat.strftime('%Y/%m/%d'), self.osItemName(file) )
		return dir

	def osItem(self, file, cre_dat, isPage=False):
		f = "%s/index.html" % self.osItemDir(file, cre_dat, isPage=isPage)
		return f

	def itemURL(self, file, cre_dat, isPage=False):
		if isPage:
			# blog "pages" have "special" handling, and their URLs do not include the date.
			dir = "%s/%s" % ( self.conf['baseURL'], self.osItemName(file) )
		else:
			dir = "%s/%s/%s" % ( self.conf['baseURL'], cre_dat.strftime('%Y/%m/%d'), self.osItemName(file) )
		return dir


