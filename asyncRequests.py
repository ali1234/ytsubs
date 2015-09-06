#!C:\Anaconda\python.exe -u
# coding=utf-8

import urllib2
from threading import Thread
import sys
from Queue import Queue

class AsyncRequests:
    def __init__(self):
        self.concurrent = 500
        self.results = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.results = []
        self.q = None

    def _do_work(self):
        while True:
            url = self.q.get()
            status, url = self._get_status(url)
            self.doSomethingWithResult(status, url)
            self.q.task_done()

    def _get_status(self, url):
        try:
            response = urllib2.urlopen(url)
            return response, url
        except:
            return "error", url

    def doSomethingWithResult(self, response, url):
        self.results.append(response)

    def run(self, url_list):
        self.q = Queue(self.concurrent * 2)
        for i in range(self.concurrent):
            t = Thread(target=self._do_work)
            t.daemon = True
            t.start()
        try:
            for url in url_list:
                self.q.put(url.strip())
            self.q.join()
        except KeyboardInterrupt:
            sys.exit(1)