import json
import random

from flask import Flask, redirect

import spotipy
import spotipy.oauth2



app = Flask(__name__)

# Flask Parameters
CLIENT_SIDE_URL = "http://127.0.0.1"
PORT = 8080
REDIRECT_URI = "{}:{}/playlists".format(CLIENT_SIDE_URL, PORT)
SCOPE = ("playlist-modify-public playlist-modify-private "
         "playlist-read-collabor ative playlist-read-private")


@app.route("/")
def index():
    """Redirect user to Spotify login/auth."""
    # TODO: Probably should add a Login page?
    sp_oauth = get_oauth()
    return redirect(sp_oauth.get_authorize_url())


@app.route("/playlists")
def display_something():
    return "Hello"


def get_oauth():
    """Return a Spotipy Oauth2 object."""
    prefs = get_prefs()
    return spotipy.oauth2.SpotifyOAuth(
        prefs["ClientID"], prefs["ClientSecret"], REDIRECT_URI, scope=SCOPE,
        cache_path=".tokens")


def get_spotify(auth_token=None):
    """Return an authenticated Spotify object."""
    oauth = get_oauth()
    token_info = oauth.get_cached_token()
    if not token_info and auth_token:
        token_info = oauth.get_access_token(auth_token)
    return spotipy.Spotify(token_info["access_token"])


def get_prefs():
    """Get application prefs plist and set secret key.
    Args:
        path: String path to a plist file.
    """
    prefs = {'ClientID' : '736c6d788bf64c14b63fd2128ab2aa3d',
             'ClientSecret': '5a2963a1c61f411ca5e9f714cebb198b'}

    return prefs



def get_names(tracks):
    """Return just the name component of a list of name/id tuples."""
    return [track[0] for track in tracks]




if __name__ == "__main__":
    app.run(debug=True, port=PORT)