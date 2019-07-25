from google.appengine.ext import ndb

class Song(ndb.Model):
    artist = ndb.StringProperty(required=True)
    track = ndb.StringProperty(required=True)
    lyrics = ndb.StringProperty(repeated=True)
