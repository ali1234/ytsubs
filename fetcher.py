# coding=utf-8

# Copyright (C) 2014 Alistair Buxton <a.j.buxton@gmail.com>
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

import urllib2
import json
from asyncRequests import AsyncRequests

class InputDataIncorrect(Exception):
    pass

class Fetcher:
    def __init__(self, username, api_key):
        self.username = username
        self.API_KEY = api_key
        self.baseurl = 'https://www.googleapis.com/youtube/v3'

    def get_subscriptions(self):
        for i in range(10):
            result = self.do_it()
            return result

    def get_channel_for_user(self, user):
        url = self.baseurl + '/channels?part=id&forUsername=' + user + '&key=' + self.API_KEY
        try:
            response = urllib2.urlopen(url)
        except:
            raise InputDataIncorrect('Something went wrong - most likely the API-Key is invalid.')

        data = self._load_json(response)

        try:
            return data['items'][0]['id']
        except IndexError:
            raise InputDataIncorrect('Username \'' + user + '\' does not exist.')

    def get_playlists(self, channel):
        # We have to get the full snippet here, because there is no other way to get the channelId
        # of the channels you're subscribed to. 'id' returns a subscription id, which can only be
        # used to subsequently get the full snippet, so we may as well just get the whole lot up front.
        url = self.baseurl + '/subscriptions?part=snippet&channelId=' + channel + '&maxResults=50&key=' + self.API_KEY
        urls = []
        next_page = ''
        while True:
            # We are limited to 50 results. If the user subscribed to more than 50 channels
            # we have to make multiple requests here which can only be fetched one after another.
            response = urllib2.urlopen(url+next_page)
            data = self._load_json(response)
            subs = []
            for i in data['items']:
                if i['kind'] == 'youtube#subscription':
                    subs.append(i['snippet']['resourceId']['channelId'])

            urls.append(self.baseurl + '/channels?part=contentDetails&id=' + '%2C'.join(subs) + '&maxResults=50&key=' + self.API_KEY)

            try:  # loop until there are no more pages
                next_page = '&pageToken='+data['nextPageToken']
            except KeyError:
                break

        # Actually getting the channel uploads requires knowing the upload playlist ID, which means
        # another request. Luckily we can bulk these 50 per request and do the requests asynchronously
        # with the urls collected from the previous requests.
        playlists = []
        with AsyncRequests() as request:
            request.run(urls)
            results = request.results
        for response in results:
            data2 = self._load_json(response)
            for i in data2['items']:
                try:
                    playlists.append(i['contentDetails']['relatedPlaylists']['uploads'])
                except KeyError:
                    pass

        return playlists

    def get_playlist_items(self, playlists):
        # We first collect all the needed urls to do all the requests asynchronously later.
        urls = []
        for playlist in playlists:
            if playlist:
                urls.append(self.baseurl + '/playlistItems?part=contentDetails&playlistId=' + playlist + '&maxResults=5&key=' + self.API_KEY)

        with AsyncRequests() as request:
            request.run(urls)
            results = request.results
        videos = []
        for response in results:
            data = self._load_json(response)
            for i in data['items']:
                if i['kind'] == 'youtube#playlistItem':
                    videos.append(i['contentDetails']['videoId'])
        return videos

    def get_real_videos(self, allitems):
        # We first collect all the needed urls to do all the requests asynchronously later.
        urls = []
        for video_ids in self.chunks(allitems, 50):
            urls.append(self.baseurl + '/videos?part=snippet%2CcontentDetails&id=' + '%2C'.join(video_ids) + '&maxResults=50&fields=items(contentDetails%2Cid%2Ckind%2Csnippet)&key=' + self.API_KEY)

        videos = []
        with AsyncRequests() as request:
            request.run(urls)
            results = request.results
        for response in results:
            data = self._load_json(response)
            videos.extend(data['items'])
        return videos

    @staticmethod
    def chunks(l, n):
        # Yield successive n-sized chunks from l.
        for i in xrange(0, len(l), n):
            yield l[i:i+n]

    @staticmethod
    def _load_json(input):
        if isinstance(input, basestring):
            return json.loads(input)
        else:
            return json.load(input)

    def do_it(self):
        # Get all upload playlists of subbed channels
        playlists = self.get_playlists(self.get_channel_for_user(self.username))

        # Get the last 5 items from every playlist
        allitems = self.get_playlist_items(playlists)

        # The playlist items don't contain the correct published date, so now
        # we have to fetch every video in batches of 50.
        allvids = self.get_real_videos(allitems)

        # Sort them by date
        sortedvids = sorted(allvids, key=lambda k: k['snippet']['publishedAt'], reverse=True)
        return sortedvids

    def query_video_information(self, video_id):
        url = self.baseurl + '/videos?part=snippet&id=' + video_id + '&key=' + self.API_KEY
        try:
            response = urllib2.urlopen(url)
            data = self._load_json(response)
            return data['items'][0]
        except:
            raise InputDataIncorrect('The video you are trying to add does not exist')
