import os
import hashlib
from datetime import datetime
import time
import sqlite3

class fsmeta:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.db_path = os.path.join(base_dir, '.bucket3', 'fsdb')
        if not os.path.isdir( self.db_path ):
            os.mkdir( self.db_path )
        self.open()
        
    def rel_path(self, abs_path):
        abs_path = os.path.abspath(abs_path) #make sure path is absolute
        return abs_path[ len(self.base_dir)+1 : ]

    def util_abs_path(self, rel_path):
        return os.path.join(self.posts_dir, rel_path)

    def open(self):
        self.db_conn = sqlite3.connect( os.path.join(self.db_path, 'db'), isolation_level="IMMEDIATE" )
        self.db_conn.row_factory = sqlite3.Row
        self.db_cur = self.db_conn.cursor()
        return self
    
    def close(self):
        self.db_conn.commit()
        self.db_conn.close()
    
    def create(self ):
        self.db_cur.execute("""
            CREATE TABLE IF NOT EXISTS file( 
                id TEXT,
                path TEXT,
                mtime INTEGER,
                lstime INTEGER,
                primary key(id))
            """)
        self.db_cur.execute("""
            CREATE TABLE IF NOT EXISTS meta( 
                key TEXT,
                value TEXT,
                primary key(key))
            """)
        self.db_conn.commit()
                    
    def hash( self, s):
        return hashlib.sha1(s).hexdigest()
        
    def meta_get(self, k, d = None):
        self.db_cur.execute("SELECT * FROM meta WHERE key=?", (k,) )
        r = self.db_cur.fetchone()
        if r:
            return r['value']
        else:
            return d
    def meta_put(self, k,v):
        self.db_cur.execute("REPLACE INTO meta VALUES(?,?)", (k, v) )
        self.db_conn.commit()

    def file_put( self, id, path, mtime, lstime ): 
        self.db_cur.execute(
            "REPLACE INTO file(id, path, mtime, lstime) VALUES(?, ?, ?, ?)",
            (id, path, int(mtime), int(lstime))
            )

    def file_put_many(self, files ):
        self.db_conn.executemany("REPLACE INTO file VALUES(?,?,?,?)", files )
            
    def file_get( self, id):
        if id:
            self.db_conn.execute("SELECT * FROM file WHERE id=?", (id, ) )
            return cur.fetchone()
            
    def file_get_all(self):
        for row in self.db_conn.execute("SELECT * FROM file"):
            yield row
    
    def file_del(self, id):
        self.db_cur.execute("DELETE FROM file WHERE id=?", (id,) )
    

    def fs_get_files_all( self, path ):
    	for path, subdirs, files in os.walk(path):
    		for name in files:
    			p = os.path.join(path,name)
    			if not os.path.islink(p):
    				t = os.path.getmtime(p)
    				yield p, int(t)

    def fs_sync( self, sub_dir ):
        path = os.path.join(self.base_dir, sub_dir)
        lstime = int( time.time() )
        ts = int(self.meta_get('last_obj_ts', 0)) # max timestamp
        count = 0
        rows = []
    	for p,t in self.fs_get_files_all(path):
            p = self.rel_path(p)
            id = self.hash(p)
            rows.append(( id, p, t, lstime ))
            count = count+1
            if count == 200:
                self.file_put_many( rows )
                rows = []
                count=0        
            if t > ts:
                ts = t
        self.file_put_many( rows )
        self.meta_put('last_obj_ts', str(int(ts)) )


    def file_get_new(self, since_ts):
        for row in self.db_conn.execute("SELECT * FROM file WHERE mtime > ?", (since_ts,) ):
            yield row

    def file_get_deleted(self, before_ts):
        for row in self.db_conn.execute("SELECT * FROM file WHERE lstime < ?", (before_ts,) ):
            yield row
    

if __name__ == '__main__':
    pass
    
    """
    Typical usage:
    
    path = 'posts'
    DB_PATH = '/Users/vrypan/Devel/module0/.db'
    db = fsmeta(DB_PATH)
    db.create()
    
    t1 = int(time.time()) # current time timestamp
    t2 = int(db.meta_get('last_obj_ts', 0)) #last object in DB timestamp
    
    # read new files from filesystem
    db.fs_sync( path ) 
    
    for f in db.file_get_new( since_ts=t2 ):
        print "[+]", f['id'], f['path'], "mtime=", f['mtime'], "lstime=", f['lstime'], "last_obj_ts=", t2

    for f in db.file_get_deleted( before_ts=t1 ):
        print "[-]", f['id'], f['path'], f['mtime'], f['lstime'], t1
        
    db.close()    
    """
