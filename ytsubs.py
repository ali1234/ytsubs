import sys
from handler import Handler
import os

if not len(sys.argv) >= 2:
    print "API-KEY needs to be first argument!"
    sys.exit(-1)
api_key = sys.argv[1]

if not len(sys.argv) >= 3:
    print "Username needs to be second argument"
    sys.exit(-1)
username = sys.argv[2]


handling = Handler(os.path.dirname(os.path.realpath(__file__)), api_key, username, 50)
handling.update_videos()
xmlstr = handling.build_rss()

if len(sys.argv) >= 4:
    filename = sys.argv[3]
    with open(filename, 'w') as f:
        f.write(xmlstr)
else:
    print xmlstr
