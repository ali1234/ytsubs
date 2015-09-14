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
from mod_python import apache
from mod_python import util
import pkgutil
from handler import Handler
from fetcher import InputDataIncorrect

def index(req):
    req.content_type = "text/html"
    start(req)
    return

def check_packages(req):
    modules = pkgutil.iter_modules()
    for each in modules:
        req.write(each[1] + "\n")

def start(req):
    form = util.FieldStorage(req)
    directory = 'YOUR_SAVE_FILE_DIRECTORY'
    api_key = 'YOUR_API_KEY'
    username = form.getfirst('user')
    if not username:
        raise InputDataIncorrect('Specify the username with the \'user\' GET attribute.')

    handling = Handler(directory, api_key, username)
    handling.add_to_watched(form.getfirst('watched'))
    handling.add_video(form.getfirst('add_video'))
    handling.save()
    req.write(handling.build_html())

    if not form.getfirst('watched'):
        handling.update_videos()
        handling.save()
        print 'Refresh the page to see new videos.'
