import spotipy
from spotipy.oauth2 import SpotifyOAuth

class Listener:
    def __init__(self, token):
        self.token = token
        self.sp = spotipy.Spotify(auth=token['access_token'])

    def getName(self):
        return self.sp.current_user()['display_name']
    
    def getID(self):
        return self.sp.current_user()['id']
    
    def getToken(self):
        return self.token
    
    def getAccess(self):
        return self.token['access_token']