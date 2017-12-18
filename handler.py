#!/usr/bin/env python
"""
Very simple HTTP server in python.
Usage::
    ./dummy-web-server.py [<port>]
Send a GET request::
    curl http://localhost
Send a HEAD request::
    curl -I http://localhost
Send a POST request::
    curl -d "foo=bar&bin=baz" http://localhost
"""
from http.server import BaseHTTPRequestHandler, HTTPServer
import pdb
import cgi

import _thread

import threading
from threading import Thread, Condition

from subprocess import Popen
from collections import deque

url_queue = deque([])
queue_cond = Condition()

url_list = open('urls', 'a')

download_dir = None

class S(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def serve_default(self):
        if not hasattr(self, 'servedata'):
            f = open('form.html')
            self.servedata = bytearray(''.join(f.readlines()), 'UTF-8')
            f.close()

        self.wfile.write(self.servedata)

    def do_GET(self):
        self._set_headers()
        self.serve_default()    

    def do_HEAD(self):
        self._set_headers()
        
    def do_POST(self):
        # Doesn't do anything with posted data
        # pdb.set_trace()
        self._set_headers()
        ctype, pdict = cgi.parse_header(self.headers.get('content-type'))
        if ctype == 'multipart/form-data':
            postvars = cgi.parse_multipart(self.rfile, pdict)
        elif ctype == 'application/x-www-form-urlencoded':
            length = int(self.headers.get('content-length'))
            postvars = cgi.parse_qs(self.rfile.read(length), keep_blank_values=1)
        else:
            postvars = {}

        if not b'url' in postvars:
            self.serve_default()

        # if not hasattr(self, 'url_list'):
        #     self.url_list = open('urls', 'a')

        # threading.enumerate()

        queue_cond.acquire()
        url_queue.append(postvars[b'url'][0].decode('UTF-8'))
        queue_cond.notify()
        
        url_list.write(url_queue[-1] + '\n')
        url_list.flush()
        
        queue_cond.release()

        tmp = open('urls')
        self.wfile.write(bytearray(''.join(tmp.readlines()), 'UTF-8'))
        tmp.close()

class DownloadThread(Thread):
    def __init__(self):
          Thread.__init__(self)

    def run (self):
        # pdb.set_trace()
        queue_cond.acquire()
        while True:
            if len(url_queue) > 0:
                url = url_queue.popleft()
                queue_cond.release()
                print("url in queue: " + url)
                # p = Popen(['mkdir', '~/dev/Downloads/'])

                if download_dir is not None: 
                    p = Popen(['axel', url, '-o', download_dir])
                else:
                    p = Popen(['axel', url])

                p.wait()
                queue_cond.acquire()
            else :
                queue_cond.wait()

def download_thread (handler):
    handler.queue_cond.acquire()
    while True:
        if len(self.url_queue) > 0:
            url = self.url_queue.popleft()
            print("url in queue: " + url)
            handler.queue_cond.release()
        else :
            handler.queue_cond.wait()



def run(server_class=HTTPServer, handler_class=S, port=80, download_dir=None):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    
    print('Starting httpd...')
    download_thread = DownloadThread()
    download_thread.start()

    httpd.serve_forever()

if __name__ == "__main__":
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    elif len(argv) == 3:
        download_dir = argv[2]
        run(port=int(argv[1]))
    else:
        run()