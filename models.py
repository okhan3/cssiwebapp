from google.appengine.ext import ndb

class Song(ndb.Model):
    artist = ndb.StringProperty(required=True)
    track = ndb.StringProperty(required=True)
    lyrics = ndb.StringProperty(repeated=True)
<<<<<<< HEAD


class User(ndb.Model):
    username = ndb.StringProperty(required=True)
    playlists = ndb.StringProperty(required=True)
    tracks = ndb.StringProperty(required=True)
=======
    views = ndb.IntegerProperty(default=1)
>>>>>>> 2110678c8dae0f23246d778867a73c93de3b4391
