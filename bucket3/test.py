from bucket3 import Bucket3v2 as Bucket3
from fsmeta import fsmeta
import b3tools
import os
import sys
import time

path = 'posts'

conf = b3tools.conf_get('/Users/vrypan/Devel/b3test2')

if not conf:
    sys.exit(1)

fsdb = fsmeta( conf['root_dir'] )
fsdb.create()

t1 = int(time.time())
t2 = int(fsdb.meta_get('last_obj_ts', 0))

fsdb.fs_sync( 'posts' ) 

b3 = Bucket3(conf = conf)
b3.db_init()

for f in fsdb.file_get_new( since_ts=t2 ):
    print "[+]", f['id'], f['path'], "mtime=", f['mtime'], "atime=", f['lstime'], "last_obj_ts=", t2
    """post = b3.fs_post_get(f['path'])
    if post:
        b3.db_post_put(post)
    """
for f in fsdb.file_get_deleted( before_ts=t1 ):
    print "[del]", f['id'], f['path'], "mtime=", f['mtime'], "atime=", f['lstime'], "last_obj_ts=", t1
    """ post_id = b3.fs_post_get_id(f['path'])
    b3.db_post_del(post_id)
    """

fsdb.close()

b3.rq_do()
