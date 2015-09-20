#!C:\Anaconda\python.exe -u
# coding=utf-8

# Copyright (C) 2015 Daniel Schäfer <ds@struckmeierfliesen.de>
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom
# the Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
# PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS
# OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import cgi
import cgitb
import sys
from handler import Handler
from fetcher import InputDataIncorrect

cgitb.enable()
directory = 'YOUR_SAVE_FILE_DIRECTORY'
api_key = 'YOUR_API_KEY'

form = cgi.FieldStorage()
username = form.getvalue('user')
if not username:
    raise InputDataIncorrect('Specify the username with the \'user\' GET attribute.')
handling = Handler(directory, api_key, username, 50)
handling.add_to_watched(form.getvalue('watched'))
handling.add_video(form.getvalue('add_video'))
handling.save()
xmlstr = handling.build_html()

f = sys.stdout
f.write("Content-type:text/html\r\n\r\n")
f.write('<!DOCTYPE html>')
f.write(xmlstr)

if not form.getvalue('watched'):
    handling.update_videos()
    print 'Refresh the page to see new videos.'
