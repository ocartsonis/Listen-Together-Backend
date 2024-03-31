import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, request, url_for, session, redirect
import psycopg2
from psycopg2.extras import Json
import threading
import SessionClass as sc, ListenerClass as lc
import json

app = Flask(__name__)

app.config['SESSION_COOKIE_NAME'] = 'Spotify Cookie'
app.secret_key = 'sydut126776t3&!@78dfsa^!'
TOKEN_INFO = 'token_info'
secret_code = ''
group_session: sc.Session

@app.route('/')
def login():
    auth_url = create_spotify_oauth().get_authorize_url()
    return redirect(auth_url)

@app.route('/user/<secret>')
def get_secret_code(secret):
    global secret_code
    secret_code = secret

    # This function will be called when someone visits /user/<username>
    return redirect('/')

@app.route('/hostSession/<session_name>/<secret>')
def create_session(session_name, secret):
    global group_session
    global secret_code
    secret_code = secret
    group_session = sc.Session(session_name)

    conn = psycopg2.connect('postgres://spotify_listen_data_user:tKsP5Ic7JJOEvB9Xv6ePnLorFvNoD40G@dpg-cneg0qmct0pc738505dg-a.oregon-postgres.render.com/spotify_listen_data')
    cursor = conn.cursor()
    #When adding listeners to this table, first serialize the listeners then add, deserialize when grabbing it from the table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) UNIQUE NOT NULL,
        session JSONB NOT NULL
    )
    """)
    cursor.execute("SELECT * FROM tokens")

    rows = cursor.fetchall()
    for row in rows:
        if row[1] == secret_code:
            group_session.addListener(lc.Listener(row[2]))
            print("added host")
    try:
        cursor.execute("INSERT INTO sessions (name, session) VALUES (%s, %s)", (session_name, psycopg2.extras.Json(group_session.getDict())))
        print("added session to database")
    except Exception as e:
        print("Exception: ", e)
    print("session hosted without errors")
    conn.commit()
    cursor.close()
    conn.close()

    group_session.createPlaylist()
    loop_thread = threading.Thread(target=run_session)
    loop_thread.daemon = True
    loop_thread.start()

    return("Session Started")

#needs rework after host session rework
@app.route('/joinSession/<session_name>/<secret>')
def join_session(session_name, secret):
    #add session stuff to join (postgresql)
    global secret_code
    global group_session
    secret_code = secret

    conn = psycopg2.connect('postgres://spotify_listen_data_user:tKsP5Ic7JJOEvB9Xv6ePnLorFvNoD40G@dpg-cneg0qmct0pc738505dg-a.oregon-postgres.render.com/spotify_listen_data')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM sessions")
    rows = cursor.fetchall()

    for row in rows:
        if row[1] == session_name:
            group_session = sc.Session(session_dict=row[2])
    
    cursor.execute("SELECT * FROM tokens")
    rows = cursor.fetchall()

    for row in rows:
        if row[1] == secret_code:
            group_session.addListener(lc.Listener(row[2]))
    print("working 1")
    group_session.createPlaylist()
    print("working 2")
    try:
        cursor.execute("DELETE FROM sessions WHERE name = %s", (session_name,))
    except Exception as e:
        print("Exception: ", e)

    cursor.execute("INSERT INTO sessions (name, session) VALUES (%s, %s)", (session_name, psycopg2.extras.Json(group_session.getDict())))
    conn.commit()
    cursor.close()
    conn.close()
    return("Session Joined")

@app.route('/redirect')
def redirect_page():
    session.clear()
    code = request.args.get('code')
    token_info = create_spotify_oauth().get_access_token(code=code, check_cache=False)
    print("info type: ", type(token_info))
    conn = psycopg2.connect('postgres://spotify_listen_data_user:tKsP5Ic7JJOEvB9Xv6ePnLorFvNoD40G@dpg-cneg0qmct0pc738505dg-a.oregon-postgres.render.com/spotify_listen_data')
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tokens (
            id SERIAL PRIMARY KEY,
            secret_code VARCHAR(100) UNIQUE NOT NULL,
            token JSONB NOT NULL
            )
    """)
    #check this tomorrow
    if(secret_code != ''):
        try:
            cursor.execute("DELETE FROM tokens WHERE secret_code = %s", (secret_code,))
        except Exception as e:
            print("Exception: ", e)
    cursor.execute("INSERT INTO tokens (secret_code, token) VALUES (%s, %s)", (secret_code, psycopg2.extras.Json(token_info)))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('listen_together', external = True))

@app.route('/listenTogether')
def listen_together():
    try:
        token = get_token()
    except:
        print("not logged in")
        return redirect('/')

    listener_test = lc.Listener(token)
    print(token, type(token))
    print(listener_test.getName())
    return(listener_test.getName())

def get_token():
    conn = psycopg2.connect('postgres://spotify_listen_data_user:tKsP5Ic7JJOEvB9Xv6ePnLorFvNoD40G@dpg-cneg0qmct0pc738505dg-a.oregon-postgres.render.com/spotify_listen_data')
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tokens (
            id SERIAL PRIMARY KEY,
            secret_code VARCHAR(100) UNIQUE NOT NULL,
            token JSONB NOT NULL
            )
    """)
    token_info = {}
    #check this tomorrow
    if(secret_code != ''):
        try:
            cursor.execute("SELECT * FROM tokens")
            rows = cursor.fetchall()

            for row in rows:
                if row[1] == secret_code:
                    token_info = row[2]
        except Exception as e:
            print("Exception: ", e)
        
    conn.commit()
    cursor.close()
    conn.close()
    if not token_info:
        redirect(url_for('login', external = False))
    now = int(time.time())
    is_expired = token_info['expires_at'] - now < 60
    if(is_expired):
        spotify_oauth = create_spotify_oauth()
        token_info = spotify_oauth.refresh_access_token(token_info['refesh_token'])

    return token_info

def create_spotify_oauth():
    return SpotifyOAuth(client_id = '66a01aec42f147a888ddb675a5f71a4e',
                        client_secret = '6c9ce3e8fcca4050921b4b69937586f6',
                        redirect_uri = url_for('redirect_page', _external = True),
                        scope = 'playlist-modify-private playlist-modify-public user-modify-playback-state user-read-playback-state user-read-currently-playing playlist-read-private playlist-read-collaborative')

def run_session():
    #global group_session
    while True:
        print("is this working?")
        time.sleep(1)
    # conn = psycopg2.connect('postgres://spotify_listen_data_user:tKsP5Ic7JJOEvB9Xv6ePnLorFvNoD40G@dpg-cneg0qmct0pc738505dg-a.oregon-postgres.render.com/spotify_listen_data')
    # print("wow")
    # cursor = conn.cursor()
    # print("huh")
    # cursor.execute("SELECT * FROM sessions")
    # rows = cursor.fetchall()
    # print("hello")
    # for row in rows:
    #     if row[1] == group_session.getName():
    #         group_session = sc.Session(session_dict=row[2])

    # group_session.syncPlaylist()
    # try:
    #     cursor.execute("DELETE FROM sessions WHERE name = %s", (group_session.getName(),))
    # except Exception as e:
    #     print("Exception: ", e)
    # cursor.execute("INSERT INTO sessions (name, session) VALUES (%s, %s)", (group_session.getName(), psycopg2.extras.Json(group_session.getDict())))
    # conn.commit()
    # cursor.close()
    # conn.close()
    return False

if __name__ == '__main__':

    app.run(debug=True)