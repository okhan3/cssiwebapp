#main.py

#Imports Section
import webapp2
import jinja2
import os
import json
from google.appengine.api import urlfetch
from models import Song

#Initialize the jinja2 environment
jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

APISEEDS_KEY = "VHl5WJoexxSgghXe4zUdqAjrfSfOdbZjCGb6BkrODi5qquF3MFPGzNrFQr1Zsj4W"

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
    api_url += artist + "/" + song
    api_url += "?apikey=" + APISEEDS_KEY
    return urlfetch.fetch(api_url)

def findSong(artist, song, songArr):
    if(len(songArr) == 0):
        return None
    for songObj in songArr:
        if artist.lower() == str(songObj.artist).lower() and song.lower() == str(songObj.track).lower():
            return {
                "artist" : songObj.artist,
                "track" : songObj.track,
                "lyrics" : songObj.lyrics,
                "status" : 200
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
        #Check if the song is in the datastore and initialize it if found
        songDict = findSong(artist_name, song_name, songArr)
        if(songDict is not None):
            song = songDict
        else:
            #Fetch the API response and its status
            apiseeds_response = fetchAPISeedsResponse(artist_name, song_name)
            response_status = apiseeds_response.status_code
            song['status'] = response_status
            #If it's successful (code 200), then decode the JSON and get the artist, track, and lyrics from it
            if int(response_status) == 200:
                apiseeds_responseJson = json.loads(apiseeds_response.content)
                result = apiseeds_responseJson['result']
                song['artist'] = result['artist']['name']
                song['track'] = result['track']['name']
                song['lyrics'] = splitLines(result['track']['text'])
                #Add the Song object to the data store if the user didn't just misspell the name of artist/song
                if(findSong(song['artist'], song['track'], songArr) == None):
                    songModel = Song(artist=song['artist'], track=song['track'], lyrics=song['lyrics'])
                    songModel.put()
        #If the song isn't found AND the API fetch is unsuccessful, nothing is printed
        input_template = jinja_env.get_template('/templates/inputlyrics.html')
        self.response.write(input_template.render(song))

#List routes
app = webapp2.WSGIApplication([
    ('/', HomePage),
    ('/inputlyrics', InputPage)
    # ('/spotifylyrics', SpotifyPage),
    # ('/popularsearch', PopularPage)
], debug=True)
