import spotipy
from spotipy.oauth2 import SpotifyOAuth
import ListenerClass as lc
import psycopg2
from psycopg2.extras import Json
import json

class Session:
    def __init__(self, name = '', session_dict={}):
        if session_dict=={}:
            self.name = name
            self.listeners = []
            self.track_uris = []
            self.total_track_differences = []
        else:
            self.name = session_dict['name']
            for listener_token in session_dict['listener_tokens']:
                self.listeners.append(lc.Listener(listener_token))
            self.track_uris = session_dict['track_uris']
            self.total_track_differences = session_dict['track_differences']

    def addListener(self, listener: lc.Listener):
        self.listeners.append(listener)

    def removeListener(self, listener: lc.Listener):
        self.listeners.remove(listener)

    def createPlaylist(self):
        for listener in self.listeners:
            sp = spotipy.Spotify(auth=listener.getAccess())
            playlist_id = ""
            for playlist in sp.current_user_playlists()['items']:
                if(playlist['name'] == self.name):
                    playlist_id = playlist['id']
            if not playlist_id:
                new_playlist = sp.user_playlist_create(user=listener.getID(), name=self.name, public=True)
                playlist_id = new_playlist['id']

    def syncPlaylist(self):
        for listener in self.listeners:
            sp = spotipy.Spotify(auth=listener.getAccess())
            current_playlists = sp.current_user_playlists()['items']
            for playlist in current_playlists:
                if playlist['name'] == self.name:
                    #make this a list that is added to or subtracted from
                    listener_tracks = sp.playlist_items(playlist_id=playlist['id'])['items']
                    listener_track_uris = []
                    for listener_track in listener_tracks:
                        listener_track_uris.append(listener_track['track']['uri'])
                    track_differences = []
                    for uri in self.track_uris:
                        if uri not in listener_track_uris:
                            track_differences.append((uri, "removed"))
                    for uri in listener_track_uris:
                        if uri not in self.track_uris:
                            track_differences.append((uri, "added"))
                    self.total_track_differences.append(track_differences)
        for differences in self.total_track_differences:
            for uri, change_type in differences:
                if change_type == "removed":
                    if uri in self.track_uris:
                        self.track_uris.remove(uri)
                if change_type == "added":
                    if uri not in self.track_uris:
                        self.track_uris.append(uri)

    def getListeners(self):
        return self.listeners
    
    def getName(self):
        return self.name
    
    def getDict(self):
        listener_tokens = []
        for listener in self.listeners:
            listener_tokens.append(listener.getToken())
        session_dict = {'name': self.name, 'listener_tokens': listener_tokens, 'track_uris': self.track_uris, 'track_differences': self.total_track_differences}
        return session_dict
        