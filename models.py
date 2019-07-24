#IGNORE THIS CODE MY PYTHON IS DUMB AND NEEDS THIS
import sys
if 'google' in sys.modules:
    del sys.modules['google']
#IGNORE THIS CODE MY PTHON IS DUMB AND NEEDS THIS

from google.appengine.ext import ndb

class Song(ndb.Model):
    artist = ndb.StringProperty(required=True)
    track = ndb.StringProperty(required=True)
    lyrics = ndb.StringProperty(repeated=True)
