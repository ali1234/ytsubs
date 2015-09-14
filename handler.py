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
from datetime import datetime
import os
from xml.dom import minidom
from xml.etree.ElementTree import Element, SubElement, tostring
from fetcher import Fetcher
import cPickle
import json


class Handler:

    def __init__(self, directory, api_key, username, max_vids):
        self.API_KEY = api_key
        self.USERNAME = username

        self.SAVE_FILE_PATH = os.path.normpath(directory + 'ytsubs_' + self.USERNAME.lower() + '.json')
        self.fetcher = Fetcher(self.USERNAME, self.API_KEY)

        self.MAX_VIDEOS = max_vids
        self.watched = []
        self.additions = []
        self.raw_videos = []
        self.load()

    def add_to_watched(self, addition):
        if addition is not None and addition not in self.watched:
            self.watched.append(addition)
            self.save()
            # TODO Maybe add a data changed flag
            # A video marked as watched can safely be deleted from the local 'own additions'.
            self._remove_from_additions(addition)

    def _remove_from_watched(self, removal):
        if removal in self.watched:
            self.watched.remove(removal)
            # TODO Maybe add a data changed flag

    def _get_vids(self):
        videos = self.fetcher.get_subscriptions()
        # TODO Maybe add a data changed flag
        self.raw_videos = videos

    # Adds a video with the id 'addition'
    def add_video(self, addition):
        # Write each video id in a separate line in a file
        if addition is not None and addition not in [add['id'] for add in self.additions]:
            self.additions.append(self.fetcher.query_video_information(addition))
            # TODO Maybe add a data changed flag
            # This ensures added videos to show up even if they have previously been marked as watched.
            self._remove_from_watched(addition)

    def _remove_from_additions(self, removal):
        # Check if the id for the video to be removed is in the 'own additions'.
        # if removal in [i['id'] for i in self.additions]:
        # Actually remove it from the list.
        self.additions = [i for i in self.additions if not i['id'] == removal]
        # TODO Maybe add a data changed flag

    def update_videos(self):
        self._get_vids()
        if reload:
            self.save()

    def save(self):
        with open(self.SAVE_FILE_PATH, 'w') as save_file:
            save_file.write(self.jsonize_data())

    def load(self):
        try:
            with open(self.SAVE_FILE_PATH, 'r') as read_file:
                data = json.load(read_file)
        except IOError:
            return

        for type, list in data.iteritems():
            if type == 'watched':
                self.watched = [v['id'] for v in list]
            elif type == 'additions':
                self.additions = list
            elif type == 'raw_videos':
                self.raw_videos = list

    def jsonize_data(self):
        data = {}
        data['watched'] = []
        for id in self.watched:
            if id is not None:
                video = {}
                video['id'] = id
                data['watched'].append(video)

        for type, list in {'additions': self.additions, 'raw_videos': [vid for vid in self.raw_videos if vid['id'] not in self.watched][:self.MAX_VIDEOS]}.iteritems():
            data[type] = []
            for addition in list:
                video = {}
                video['id'] = addition['id']
                video['snippet'] = {}
                video['snippet']['title'] = addition['snippet']['title']
                video['snippet']['publishedAt'] = addition['snippet']['publishedAt']
                #video['snippet']['description'] = addition['snippet']['description']
                video['snippet']['categoryId'] = addition['snippet']['categoryId']
                video['snippet']['channelTitle'] = addition['snippet']['channelTitle']
                video['snippet']['channelId'] = addition['snippet']['channelId']

                data[type].append(video)
        return json.dumps(data)

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
        hidden = SubElement(add_form, 'input', {'type': 'hidden', 'name': 'user', 'value': self.USERNAME})
        submit = SubElement(add_form, 'input', {'type': 'submit', 'value': 'Add'})

        all_videos = self.additions + self.raw_videos
        if not all_videos:
            error_message = SubElement(body, 'h2')
            error_message.text = 'No videos were saved - new ones are being loaded.'

        all_videos = [v for v in all_videos if v['id'] not in self.watched]
        i = 0
        for v in all_videos:
            i+=1
            published_date = datetime.strptime(v['snippet']['publishedAt'], "%Y-%m-%dT%H:%M:%S.000Z")
            # A maximum of MAX_VIDEOS which are newer than 7 days will be shown
            if (datetime.now() - published_date).days > 7 or i > self.MAX_VIDEOS:
                break
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
