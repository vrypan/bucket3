===========
Bucket3
===========

bucket3 is a simple, blog aware, static site generator written in python. It reads your content and spits out a complete, static website suitable for serving with Apache or your favorite web server.

bucket3 would like to become a virtual “information bucket” where you throw 
pieces of information (texts, images, audio, etc), and presents them in a nice 
blog-like format.

Quick intro
=========

1. pip install bucket3

2. mkdir myblog ; mkdir myblog/posts ; mkdir myblog/html

3. cd myblog; bucket3 --new-conf

4. Edit conf.yaml or create a new one (see conf.yaml.example)

5. bucket3 --new posts/hellowworld.md

5. bucket3.py --conf=conf.yaml --skel --new-posts

6. You should now have your whole blog under "html" (as defined in your conf file).

7. Upload the files to your server.

Examples
------------

conf.bucket3com.yaml, _themes/bucket3com and the posts under posts/ are the source of http://www.bucket3.com/ 

http://blog.vrypan.net/ is also generated using bucket3.

License
=========

bucket3 is distributed under the MIT LICENSE.

Copyright
=========

Panayotis Vryonis, http://vrypan.net/

See also
=========
If you are not familiar with the idea of a static HTML blog, visit https://github.com/mojombo/jekyll they've done a much better way at explaining it! (the intro is actually a copy from jekyll's README file)
