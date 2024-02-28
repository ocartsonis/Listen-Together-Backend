import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, request, url_for, session, redirect

app = Flask(__name__)

app.config['SESSION_COOKIE_NAME'] = 'Spotify Cookie'
app.secret_key = 'sydut126776t3&!@78dfsa^!'
TOKEN_INFO = 'token_info'

@app.route('/')
def login():
    auth_url = create_spotify_oauth().get_authorize_url()
    return redirect(auth_url)

@app.route('/redirect')
def redirect_page():
    session.clear()
    code = request.args.get('code')
    token_info = create_spotify_oauth().get_access_token(code)
    session[TOKEN_INFO] = token_info
    return redirect(url_for('listen_together', external = True))

@app.route('/listenTogether')
def listen_together():
    try:
        token_info = get_token()
    except:
        print("not logged in")
        return redirect('/')
    return("oath successful")

def get_token():
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        redirect(url_for('login', external = False))
    now = int(time.time())
    is_expired = token_info['expires_at'] - now < 60
    if(is_expired):
        spotify_oauth = create_spotify_oauth
        token_info = spotify_oauth.refresh_access_token(token_info['refesh_token'])
    return token_info

def create_spotify_oauth():
    return SpotifyOAuth(client_id = '66a01aec42f147a888ddb675a5f71a4e',
                        client_secret = '6c9ce3e8fcca4050921b4b69937586f6',
                        redirect_uri = url_for('redirect_page', _external = True),
                        scope = 'playlist-modify-private playlist-modify-public user-modify-playback-state user-read-playback-state user-read-currently-playing')

if __name__ == '__main__':
    app.run()