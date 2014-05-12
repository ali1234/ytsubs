#!/usr/bin/env python

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
import itertools
import sys
from xml.etree.ElementTree import Element, SubElement, Comment, tostring

baseurl = 'https://www.googleapis.com/youtube/v3'
my_key = 'youtube secret server key'

def get_channel_for_user(user):
    url = baseurl + '/channels?part=id&forUsername='+ user + '&key=' + my_key
    response = urllib2.urlopen(url)
    data = json.load(response)
    return data['items'][0]['id']

def get_playlists(channel):
    playlists = []
    # we have to get the full snippet here, because there is no other way to get the channelId
    # of the channels you're subscribed to. 'id' returns a subscription id, which can only be
    # used to subsequently get the full snippet, so we may as well just get the whole lot up front.
    url = baseurl + '/subscriptions?part=snippet&channelId='+ channel + '&maxResults=50&key=' + my_key

    next_page = ''
    while True:
        # we are limited to 50 results. if the user subscribed to more than 50 channels
        # we have to make multiple requests here.
        response = urllib2.urlopen(url+next_page)
        data = json.load(response)
        subs = []
        for i in data['items']:
            if i['kind'] == 'youtube#subscription':
                subs.append(i['snippet']['resourceId']['channelId'])

        # actually getting the channel uploads requires knowing the upload playlist ID, which means
        # another request. luckily we can bulk these 50 at a time.
        purl = baseurl + '/channels?part=contentDetails&id='+ '%2C'.join(subs) + '&maxResults=50&key=' + my_key
        response = urllib2.urlopen(purl)
        data2 = json.load(response)
        for i in data2['items']:
            try:
                playlists.append(i['contentDetails']['relatedPlaylists']['uploads'])
            except KeyError:
                pass

        try: # loop until there are no more pages
            next_page = '&pageToken='+data['nextPageToken']
        except KeyError:
            break

    return playlists

def get_videos(playlist):
    videos = []

    if playlist:
        # get the last 5 videos uploaded to the playlist
        url = baseurl + '/playlistItems?part=snippet&playlistId='+ playlist + '&maxResults=5&key=' + my_key
        response = urllib2.urlopen(url)
        data = json.load(response)    
        for i in data['items']:
            if i['kind'] == 'youtube#playlistItem':
                videos.append(i['snippet'])

    return videos

username = sys.argv[1]

# get all upload playlists of subbed channels
playlists = get_playlists(get_channel_for_user(username))

# get the last 5 videos from every playlist
allvids = []
for p in playlists:
    allvids.extend(get_videos(p))

# sort them by date
sortedvids = sorted(allvids, key=lambda k: k['publishedAt'], reverse=True)


# build the rss
rss = Element('rss')
rss.attrib['version'] = '2.0'
channel = SubElement(rss, 'channel')
title = SubElement(channel, 'title')
title.text = 'Youtube subscriptions for ' + username
link = SubElement(channel, 'link')
link.text = 'http://www.youtube.com/'

# add the most recent 20
for v in sortedvids[:20]:
    item = SubElement(channel, 'item')
    title = SubElement(item, 'title')
    title.text = v['title']
    link = SubElement(item, 'link')
    link.text = 'http://youtube.com/watch?v=' + v['resourceId']['videoId']
    description = SubElement(item, 'description')
    description.text = v['description']

f = open(sys.argv[2], 'w')
f.write('<?xml version="1.0" encoding="UTF-8" ?>')
f.write(tostring(rss))
f.close()

