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

class HomePage(webapp2.RequestHandler):
    def get(self): #for a get request
        home_template = the_jinja_env.get_template('/templates/home.html')
        self.response.write(home_template.render())

app = webapp2.WSGIApplication([
    ('/', HomePage)#,
    # ('/inputtolyrics', InputPage),
    # ('/spotifytolyrics', SpotifyPage),
    # ('/popularsearch', PopularPage)
], debug=True)
