import spotipy
from spotipy.oauth2 import SpotifyOAuth
import ListenerClass as lc

class Session:
    def __init__(self, name):
        self.name = name
        self.listeners = []
        self.track_uris = []
        self.total_track_differences = []

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
            print(type(listener))
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
        