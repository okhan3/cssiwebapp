#main.py

#Thanks to https://medium.com/@masaok/gae-spotifyoautherror-none-6bac60ee3837 ... whoever you are

#TODO: update lyricsinput so it appears only when status == 200
#TODO: Display error on spotify upon not finding lyrics
#TODO: Styling on spotify page (fixed search button,
#rectangular boxes for results, borders, styling lyrics, and inserting giraffe img)

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

#Omar's key for apiseeds
APISEEDS_KEY = "VHl5WJoexxSgghXe4zUdqAjrfSfOdbZjCGb6BkrODi5qquF3MFPGzNrFQr1Zsj4W"

#Spotify Client Flow stuff (client id/secret probably should be exported, but whatever...)
CLIENT_ID = 'a3af3476e5f24441ba77767bdd13f518'
CLIENT_SECRET = '08aee8a23fd148f3a790fe4116edecb1'
CLIENT_CREDENTIALS_MANAGER = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
spotify = spotipy.Spotify(client_credentials_manager=CLIENT_CREDENTIALS_MANAGER)

username = ""

#Merges dictionaries x and y into z
def merge_dicts(x, y):
    z = x.copy()
    z.update(y)
    return z

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

#Look up artist/track in the datastore (will return dictionary info if getKey is false, otherwise returns key of the specific Song object)
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

#Look up user in the datastore
def findUser(user, userArr):
    if(len(userArr) == 0):
        return None
    for userObj in userArr:
        if user.lower() == str(userObj.username).lower():
            return {
                "username" : userObj.username,
                "playlist_names" : userObj.playlist_names,
                "playlist_tracklists" : json.loads(userObj.playlist_tracklists),
                "status": 200
                }
    return None

def getSpotifyDetails(spotify_username):
    spotifyDetails = {}
    #Attempt to get the specified user's playlist info
    try:
        playlists = spotify.user_playlists(spotify_username)
    except:
        spotifyDetails['status'] = 1
        return spotifyDetails
    #If no playlists are created and made public, do nothing
    if(len(playlists['items']) == 0):
        spotifyDetails['status'] = 2
        return spotifyDetails
    #Record a successful status, process public playlists, and return details
    spotifyDetails['status'] = 200
    return merge_dicts(spotifyDetails, processPlaylists(playlists['items'], spotify_username))

def processPlaylists(playlists, spotify_username):
    playlistInfo = {}
    playlist_names = []
    playlist_tracklists = []
    tracklist = []

    #Loop through all available public playlists
    for playlist in playlists:
        #Append the name of the playlist to the list of playlist names
        playlist_names.append(playlist['name'])
        #Loop through all tracks in the playlist URI
        for track in spotify.user_playlist_tracks(spotify_username, playlist['uri'])['items']:
            # Loop through the details in the track and append a tuple of the track name/artist
            try:
                tracklist.append((track['track']['name'], track['track']['artists'][0]['name']))
            except:
                playlistInfo['status'] = -1
                return playlistInfo
        #Add the single tracklist to the list of playlist tracklists
        playlist_tracklists.append(tracklist)
        tracklist = []

    playlistInfo['playlist_names'] = playlist_names
    playlistInfo['playlist_tracklists'] = playlist_tracklists
    playlistInfo['username'] = spotify_username

    return playlistInfo

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
                song['track'] = ''
                song['lyrics'] = ''
        # If the song isn't found AND the API fetch is unsuccessful, nothing is printed
        input_template = jinja_env.get_template('/templates/inputlyrics.html')
        self.response.write(input_template.render(song))

class SpotifyPage(webapp2.RequestHandler):
    def get(self):
        spotify_template = jinja_env.get_template('/templates/spotifylyrics.html')
        self.response.write(spotify_template.render())
    def post(self):
        dictionary = {}
        #Execute this code if the user is entering their spotify username
        if str(self.request.get("song-select")) == "":
            spotify_username = str(self.request.get("spotify_username")).strip()
            username = spotify_username
            userArr = User.query().fetch()
            dictionary = findUser(spotify_username, userArr)
            #If the user is not found in the datastore, get their spotify details
            if(dictionary is None):
                dictionary = getSpotifyDetails(spotify_username)
                # If the playlists are successfully gathered, add the user to the datastore for quick access
                if(int(dictionary['status']) == 200):
                    userModel = User(username=spotify_username, playlist_names = dictionary['playlist_names'], playlist_tracklists = json.dumps(dictionary['playlist_tracklists']))
                    userModel.put()
        else: #Else if they're choosing a song execute this code
            #Retrieve the artist/song from the user
            req = str(self.request.get("song-select"))
            song_name = str(req[:req.index(" /// ")]).strip()
            artist_name = str(req[req.index(" /// ")+5:req.index(" *** ")]).strip()
            spotify_username  = str(req[req.index(" *** ")+5:]).strip()
            dictionary = findUser(spotify_username, User.query().fetch())
            #Fetch the apiseeds response
            apiseeds_response = fetchAPISeedsResponse(artist_name, song_name)
            response_status = apiseeds_response.status_code
            #Continue if the song is fetched successfully
            if(int(response_status) == 200):
                apiseeds_responseJson = json.loads(apiseeds_response.content)
                result = apiseeds_responseJson['result']
                dictionary['artist'] = result["artist"]["name"]
                dictionary['track'] = result["track"]["name"]
                dictionary['lyrics'] = splitLines(result['track']['text'])
                dictionary['display'] = True
                if(findSong(dictionary['artist'], dictionary['track'], Song.query().fetch(), False) == None):
                    songModel = Song(artist=dictionary['artist'], track=dictionary['track'], lyrics=dictionary['lyrics'])
                    songModel.put()
                else:
                    songKey = Song.query().filter(Song.artist == dictionary['artist'] and Song.track == dictionary['track'])
                    songEntity = songKey.get()
                    songEntity.views += 1
                    songEntity.lyrics = dictionary['lyrics']
                    songEntity.put()
            else:
                dictionary['display'] = False
        spotify_template = jinja_env.get_template('/templates/spotifylyrics.html')
        self.response.write(spotify_template.render(dictionary))

class PopularPage(webapp2.RequestHandler):
    def get(self):
        order = Song.query().order(-Song.views).fetch(5)
        popularList = {
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
