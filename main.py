#main.py
# the import section
import webapp2
import jinja2
import os
import json
from google.appengine.api import urlfetch

the_jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

API_KEY = "VHl5WJoexxSgghXe4zUdqAjrfSfOdbZjCGb6BkrODi5qquF3MFPGzNrFQr1Zsj4W"

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

class HomePage(webapp2.RequestHandler):
    def get(self): #for a get request
        home_template = the_jinja_env.get_template('/templates/home.html')
        self.response.write(home_template.render())

class InputPage(webapp2.RequestHandler):
    def get(self):
        input_template = the_jinja_env.get_template('/templates/inputlyrics.html')
        self.response.write(input_template.render({"artist": ""}))
    def post(self):
        api_url = "https://orion.apiseeds.com/api/music/lyric/"
        api_url += self.request.get("artist_name") + "/"
        api_url += self.request.get("song_name")
        api_url += "?apikey=" + API_KEY
        apiseeds_response = urlfetch.fetch(api_url)
        status = apiseeds_response.status_code
        song = {
            "status" : status,
        }
        if int(status) == 200:
            apiseeds_responseJson = json.loads(apiseeds_response.content)
            result = apiseeds_responseJson['result']
            song['artist'] = result['artist']['name']
            song['track'] = result['track']['name']
            song['lyrics'] = splitLines(result['track']['text'])
        input_template = the_jinja_env.get_template('/templates/inputlyrics.html')
        self.response.write(input_template.render(song))

app = webapp2.WSGIApplication([
    ('/', HomePage),
    ('/inputlyrics', InputPage)
    # ('/spotifylyrics', SpotifyPage),
    # ('/popularsearch', PopularPage)
], debug=True)
