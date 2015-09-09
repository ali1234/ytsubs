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

import os
from xml.dom import minidom
from xml.etree.ElementTree import Element, SubElement, tostring
from fetcher import Fetcher
import cPickle


class Handler:

    def __init__(self, directory, api_key, username):
        self.API_KEY = api_key
        self.USERNAME = username

        self.DIRECTORY = directory
        self.WATCHED_PATH = os.path.normpath(self.DIRECTORY + self.USERNAME.lower() + '_watchedVids.txt')
        self.RAW_PATH = os.path.normpath(self.DIRECTORY + self.USERNAME.lower() + '_rawData.txt')
        self.ADDITIONS_PATH = os.path.normpath(self.DIRECTORY + self.USERNAME.lower() + '_ownAdditions.txt')

        self.fetcher = Fetcher(self.USERNAME, self.API_KEY)
        self.watched = self._get_watched_list()
        self.sortedvids = []


    def _get_watched_list(self):
        try:
            with open(self.WATCHED_PATH, 'r') as watchedFile:
                return cPickle.load(watchedFile)
        except EOFError:
            return []
        except IOError:
            open(self.WATCHED_PATH, 'wb').close()
            return []

    def add_to_watched(self, addition):
        if addition is None:
            return
        if addition not in self.watched:
            self.watched.append(addition)
        with open(self.WATCHED_PATH, 'w') as watchedFile:
            cPickle.dump(self.watched, watchedFile)
        # A video marked as watched can safely be deleted from the local 'own additions'.
        self._remove_from_own_additions(addition)

    def _remove_from_watched(self, removal):
        if removal in self.watched:
            self.watched.remove(removal)
        with open(self.WATCHED_PATH, 'w') as watchedFile:
            cPickle.dump(self.watched, watchedFile)

    def _get_vids(self, reload):
        try:
            with open(self.RAW_PATH, 'r') as rawFile:
                videos = cPickle.load(rawFile)
        except:
            videos = []

        if reload:
            videos = self.fetcher.get_subscriptions()
            if videos:
                with open(self.RAW_PATH, 'w') as rawFile:
                    cPickle.dump(videos, rawFile)
        return videos

    def get_own_additions(self):
        try:
            with open(self.ADDITIONS_PATH, 'r') as additionFile:
                ids = [line.strip() for line in additionFile]
            additions = [self.fetcher.query_video_information(video_id) for video_id in ids]
            return additions
        except EOFError:
            return []
        except IOError:
            open(self.ADDITIONS_PATH, 'wb').close()
            return []

    def add_own_video(self, addition):
        # Write each video id in a separate line in a file
        if addition is None:
            return
        with open(self.ADDITIONS_PATH, 'a') as additionFile:
            additionFile.write(addition + os.linesep)
        # This ensures added videos to show up even if they have previously been marked as watched.
        self._remove_from_watched(addition)

    def _remove_from_own_additions(self, removal):
        additions = self.get_own_additions()
        # Check if the id for the video to be removed is in the 'own additions'.
        if removal in [i['id'] for i in additions]:
            # Actually remove it from the list.
            additions = [i for i in additions if not i['id'] == removal]
            with open(self.ADDITIONS_PATH, 'w') as additionFile:
                for vid in additions:
                    if len(vid['id']) > 0:
                        additionFile.write("%s\n" % vid['id'])

    def load_videos(self, reload):
        self.sortedvids = self.get_own_additions() + self._get_vids(reload)

    def build_html(self):
        # Display the videos in a format similar to the YouTube feed.
        html = Element('html')
        head = SubElement(html, 'head')
        doc_title = SubElement(head, 'title')
        doc_title.text = 'Subscriptions'
        style = SubElement(head, 'style')
        style.text = '.float_left { float: left; }' \
                     '.container { float: left; width: 196px; height: 200px; margin: 5px; }' \
                     '.thumbnail_link { display: block; text-decoration: none}' \
                     '.thumbnail { display: block; width: 196px; height: 110px; }' \
                     '.block_clear { display: block; clear: both; }' \
                     '.watched { color: darkgrey;  font-style: italic; float: right; }' \
                     '#header { margin: auto; width: 250px;}'

        body = SubElement(html, 'body')
        header = SubElement(body, 'div', {'id': 'header'})
        add_form = SubElement(header, 'form', {'method': 'get'})
        input = SubElement(add_form, 'input', {'type': 'text', 'name': 'add_video', 'placeholder': 'Enter video URL'})
        submit = SubElement(add_form, 'input', {'type': 'submit', 'value': 'Add'})

        if not self.sortedvids:
            error_message = SubElement(body, 'h2')
            error_message.text = 'No videos were saved - new ones are being loaded.'

        for v in self.sortedvids[:50]:
            if v['id'] in self.watched:
                continue
            video_title = v['snippet']['title']
            container = SubElement(body, 'div', {'class': 'container'})

            link = SubElement(container, 'a',
                              {'href': 'http://youtube.com/watch?v=' + v['id'], 'class': 'thumbnail_link', 'title': video_title})

            thumbnail = SubElement(link, 'img',
                                   {'alt': v['snippet']['title'], 'src': 'http://i.ytimg.com/vi_webp/' + v['id'] + '/mqdefault.webp', 'class': 'thumbnail'})

            title = SubElement(link, 'span')
            title.text = video_title[:40] + (video_title[40:] and '...')

            uploader = SubElement(container, 'span')
            uploader.text = v['snippet']['channelTitle']

            mark_watched = SubElement(container, 'a', {'href': '?watched=' + v['id'] + '&user=' + self.USERNAME, 'class': 'watched'})
            mark_watched.text = 'watched'

        reload_button = SubElement(body, 'a', {'href': '?user=' + self.USERNAME, 'class': 'block_clear'})
        reload_button.text = 'Reload'
        return minidom.parseString(tostring(html)).toprettyxml(indent="   ").encode('utf-8')
