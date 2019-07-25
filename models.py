from google.appengine.ext import ndb

class Song(ndb.Model):
    artist = ndb.StringProperty(required=True)
    track = ndb.StringProperty(required=True)
    lyrics = ndb.StringProperty(repeated=True)


class User(ndb.Model):
    username = ndb.StringProperty(required=True)
    playlists = ndb.StringProperty(required=True)
    tracks = ndb.StringProperty(required=True)
