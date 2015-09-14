## Custom YouTube Subscription Box
This python script will fetch the latest subscription videos for a 
named Youtube user and display it in a grid just like the YouTube Subscription Box.

For plain CGI use:

    localhost/index_cgi.py?user=USERNAME
    
or for MOD_PYTHON:
    
    localhost/index_mod_python.py?user=USERNAME

If you use your own framework use the following code snippet to generate a `Fetcher` Object and generate the HTML:

    handling = Handler(directory, api_key, username, 50)
    html_string = handling.build_html()
    
`directory` specifies where the savefiles should be saved to.  
To update the videos and save the changes(including additions and 'watched' markings) use the following methods:

    handling.update_videos()
    handling.save()

To mark a video as watched or add a video to the list call these methods:

    handling.add_to_watched(VIDEO_ID)
    handling.add_video(VIDEO_ID)

### Features:
* Query videos for all the subscriptions of a specific user
* Parallelize of most requests (because the performance of the new v3 API is abysmal)
* Save subscription videos for each user as JSON
* Mark videos as watched and they will not show up in the HTML again
* Add other videos to the list 

Parallelization brings the querying of all videos down to a few seconds
for even hundreds of subscriptions which makes it possible to be done in a webpage.
It will only be done if no video has been marked as watched to prevent unnecessary requests.
---
The script uses the Youtube V3 API which requires you to create an 
application on the Google developer console before you can make 
requests. After you make the application you must enable
'YouTube Data API v3' access and create a server API key.

This is all explained here:  
https://developers.google.com/youtube/registering_an_application

Note that the API key owner does not need to be the same user you want
to get subscription videos for. The API allows you to read subscriptions
of any user who hasn't set their account to private.

The V3 API is incredibly inefficient at getting this information.
The script will make 2 API calls for every 50 subscriptions you have
and then it will make another API call for each subscription to get
the actual videos - THEN it makes another API call for each 50 videos
to get the real publication time.  
The fetching of the subscriptions can only be done in batches of 50
one after another but for everything after that it is possible to
query multiple batches of 50 at the same time. This yields a tremendous
speedup of about a factor of 20.

If you have 100 subscriptions this script will use
around 500 API "units" each time you call it. You are allowed to use
50,000,000 units per day so you should not run into the limits
if you are only updating hourly, even if you have thousands of subs.