#main.py

#TODO: possibly change findSong() function using query().filter()?
#TODO: update styling for the home page and add relevant text
#TODO: SPOTIFY STUFF?!?!?!?
#TODO: display error message when search for lyrics fails?
#TODO: use https://urllib3.readthedocs.io/en/latest/reference/urllib3.contrib.html instead of URLFETCH?????
#Thanks to https://medium.com/@masaok/gae-spotifyoautherror-none-6bac60ee3837 ... whoever you are

#Imports Section
import webapp2
import jinja2
import os
import json
import spotipy
import requests_toolbelt.adapters.appengine
from spotipy.oauth2 import SpotifyClientCredentials
from google.appengine.api import urlfetch
from models import Song
from models import User
from collections import Counter
#Just fixes whatever the issue was... leave it in -_-
requests_toolbelt.adapters.appengine.monkeypatch()

#Initialize the jinja2 environment
jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

APISEEDS_KEY = "VHl5WJoexxSgghXe4zUdqAjrfSfOdbZjCGb6BkrODi5qquF3MFPGzNrFQr1Zsj4W"

client_credentials_manager = SpotifyClientCredentials(client_id='a3af3476e5f24441ba77767bdd13f518', client_secret='08aee8a23fd148f3a790fe4116edecb1')
spotify = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

username = ""

#Splits the lyrics provided by apiseeds by line into an array
def splitLines(text):
    lines = []
    while True:
        breakIndex = text.find("\n")
        if breakIndex == -1:
            break
        lines.append(text[0:breakIndex])
        text = text[breakIndex + 1: len(text)]
    lines.append(text)
    return lines

def fetchAPISeedsResponse(artist, song):
    api_url = "https://orion.apiseeds.com/api/music/lyric/"
    api_url += artist.replace(" ", "%20") + "/" + song.replace(" ", "%20")
    api_url += "?apikey=" + APISEEDS_KEY
    return urlfetch.fetch(api_url)

def findSong(artist, track, songArr, getKey):
    song = {}
    if(len(songArr) == 0):
        return None
    for songObj in songArr:
        if artist.lower() == str(songObj.artist).lower() and track.lower() == str(songObj.track).lower():
            song['artist'] = songObj.artist
            song['track'] = songObj.track
            song['lyrics'] = songObj.lyrics
            song['views'] = songObj.views
            song['status'] = 200
            if(not getKey):
                return song
            else:
                return Song.query(Song.artist == song['artist'] and Song.track == song['track'])
    return None

def findUser(user, userArr):
    if(len(user) == 0):
        return None
    for users in userArr:
        if user.lower() == str(users.username).lower():
            return {
                "tracks" : users.tracks,
                "playlists" : users.playlists,
                }
    return None

class HomePage(webapp2.RequestHandler):
    def get(self):
        home_template = jinja_env.get_template('/templates/home.html')
        self.response.write(home_template.render())

class InputPage(webapp2.RequestHandler):
    def get(self):
        #Loads the inputlyrics.html template with a dictionary key/value "artist": "" (so "" doesn't randomly appear)
        input_template = jinja_env.get_template('/templates/inputlyrics.html')
        self.response.write(input_template.render({"artist": ""}))
    def post(self):
        #Get the user form information, fetch all Song objects from the Google Database, and declare the song dictionary
        artist_name = str(self.request.get("artist_name")).strip()
        song_name = str(self.request.get("song_name")).strip()
        songArr = Song.query().fetch()
        song = {}
        # Check if the song is in the datastore and initialize it if found
        songDict = findSong(artist_name, song_name, songArr, False)
        if(songDict is not None):
            songKey = findSong(artist_name, song_name, songArr, True)
            songEntity = songKey.get()
            songEntity.views += 1
            songEntity.lyrics = songDict['lyrics']
            songEntity.put()
            song = songDict
        else:
            # Fetch the API response and its status
            apiseeds_response = fetchAPISeedsResponse(artist_name, song_name)
            response_status = apiseeds_response.status_code
            song['status'] = response_status
            # If it's successful (code 200), then decode the JSON and get the artist, track, and lyrics from it
            if int(response_status) == 200:
                apiseeds_responseJson = json.loads(apiseeds_response.content)
                result = apiseeds_responseJson['result']
                song['artist'] = result["artist"]["name"]
                song['track'] = result["track"]["name"]
                song['lyrics'] = splitLines(result['track']['text'])
                # song.update("frequency"+1)
                # Add the Song object to the data store if the user didn't just misspell the name of artist/song
                if(findSong(song['artist'], song['track'], songArr, False) == None):
                    songModel = Song(artist=song['artist'], track=song['track'], lyrics=song['lyrics'])
                    songModel.put()
                else:
                    songKey = Song.query().filter(Song.artist == song['artist'] and Song.track == song['track'])
                    songEntity = songKey.get()
                    songEntity.views += 1
                    songEntity.lyrics = song['lyrics']
                    songEntity.put()
            else:
                song['error'] = "We could not find that song, try again."
        # If the song isn't found AND the API fetch is unsuccessful, nothing is printed
        input_template = jinja_env.get_template('/templates/inputlyrics.html')
        self.response.write(input_template.render(song))

class SpotifyPage(webapp2.RequestHandler):
    def get(self):
        spotify_template = jinja_env.get_template('/templates/spotifylyrics.html')
        self.response.write(spotify_template.render())
    def post(self):
        if self.request.get('form_name') == 'user':
            global username
            spotify_username = str(self.request.get("spotify_username")).strip()
            if spotify_username == "":
                spotify_username = username
            else:
                username = spotify_username
            userArr = User.query().fetch()
            info = findUser(spotify_username, userArr)
            if info == None:
                playlists = spotify.user_playlists(spotify_username)
                playlist_list = playlists['items']
                uri = []
                name = []
                tracks = []
                tracknames = []
                playlistsss = []
                for playlist in playlist_list:
                    uri.append(playlist['uri'])
                    name.append(playlist['name'])
                    playlistsss.append(playlist)
                for id in uri:
                    tracks.append(spotify.user_playlist_tracks('joeychin01', id)['items'])
                for tracklist in tracks:
                    trackoftrack = []
                    for track in tracklist:
                        trackoftrack.append((track['track']['name'], track['track']['artists'][0]['name']))
                    tracknames.append(trackoftrack)
                playlist = {
                    'names': name,
                    'uris': uri,
                    'tracknames': tracknames,
                    'length': int(len(name))
                }
                user1 = User(username=spotify_username, tracks=tracknames, playlists=playlistsss)
                user1.put()
                spotify_template = jinja_env.get_template('/templates/spotifylyrics.html')
                self.response.write(spotify_template.render(playlist))
            else:
                uri = []
                name = []
                for playlist in info['playlists']:
                    uri.append(playlist['uri'])
                    name.append(playlist['name'])
                playlist = {
                    'names': name,
                    'uris': uri,
                    'tracknames': info['tracks'],
                    'length': int(len(info['playlists']))
                }
                spotify_template = jinja_env.get_template('/templates/spotifylyrics.html')
                self.response.write(spotify_template.render(playlist))
        else:
            tup = self.request.get('track')
            song_name = tup[0]
            artist_name = tup[1]

class PopularPage(webapp2.RequestHandler):
    def get(self):
        order = Song.query().order(-Song.views).fetch(5)
        popularList={
            "list" : order
            }
        popular_template = jinja_env.get_template('/templates/popularsearch.html')
        self.response.write(popular_template.render(popularList))

#List routes
app = webapp2.WSGIApplication([
    ('/', HomePage),
    ('/inputlyrics', InputPage),
    ('/spotifylyrics', SpotifyPage),
    ('/popularsearch', PopularPage)
], debug=True)
