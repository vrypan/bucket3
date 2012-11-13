import os
import yaml

class conf():
	def locate(self, cpath = None):
		if cpath:
			# more testing need to be done here.
			return cpath
		confpath = None
		cwd = os.getcwd()
		h,t = os.path.split(cwd) # head, tail

		while h != os.sep:
			if os.path.isdir(
					os.path.join(h,t,'.bucket3')
					):
				confpath = os.path.join(h,t)
				break
			else:
				h,t = os.path.split(h)

		if not confpath:
			print 'bucket3.tools.Conf.locate: Unable to locate a bucket3 configuration.'
			return None
		else:
			return confpath
	
	def get(self, cpath = None):
		cpath = self.locate(cpath)
		if not cpath:
			print 'bucket3.tools.Conf.get: Unable to read bucket3 configuration.'
			return None

		conf_file = os.path.join(toppath, '.bucket3', 'conf.yaml')
		conf = yaml.load(open(conf_file,mode='r').read())

		return conf

