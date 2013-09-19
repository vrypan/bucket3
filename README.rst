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

2. mkdir myblog

3. cd myblog; bucket3 init

4. Edit .bucket3/conf.yaml

5. cd posts; bucket3 new hello-world-1 

6. Edit the file generated, and add some text.

7. bucket3 update

8. You should now have your whole blog under "html" (as defined in your conf file).

9. Upload the files under html/ to your server.

Examples
------------

Check out the source of http://www.bucket3.com/ at https://github.com/vrypan/www.bucket3.com

http://blog.vrypan.net/ is also generated using bucket3.

License
=========

bucket3 is distributed under the MIT LICENSE.

Copyright
=========

Panayotis Vryonis, http://www.vrypan.net/

See also
=========
If you are not familiar with the idea of a static HTML blog, visit https://github.com/mojombo/jekyll they've done a much better way at explaining it! (the intro is actually a copy from jekyll's README file)
