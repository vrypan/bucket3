
class bucket():
	def __init__(self, conf):
		self.conf = conf
		return self

	def osItemName(self, file):
		return file.split('/')[-1].rpartition('.')[0]

	def osItemDir(self, file, cre_dat):
		dir = "%s/%s/%s" % ( self.conf['htmlDir'], cre_dat.strftime('%Y/%m/%d'), self.osItemName(file) )
		return dir

	def osItem(self, file, cre_dat):
		f = "%s/index.html" % self.osItemDir(file, cre_dat)
		return f

	def itemURL(self, file, cre_dat):
		dir = "%s/%s/%s" % ( self.conf['baseURL'], cre_dat.strftime('%Y/%m/%d'), self.osItemName(file) )
		return dir


