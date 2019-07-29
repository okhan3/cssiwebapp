from google.appengine.ext import ndb

class Song(ndb.Model):
    artist = ndb.StringProperty(required=True)
    track = ndb.StringProperty(required=True)
    lyrics = ndb.StringProperty(repeated=True)
    views = ndb.IntegerProperty(default=1)

class User(ndb.Model):
    username = ndb.StringProperty(required=True)
    playlist_names = ndb.StringProperty(repeated=True)
    playlist_tracklists = ndb.StringProperty(indexed=False)
