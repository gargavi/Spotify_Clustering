import pandas as pd
from flask import Flask, redirect, request, render_template, session, url_for
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import SelectMultipleField, TextAreaField, SubmitField


import numpy as np
import spotipy
import spotipy.oauth2


#E6E6FA
app = Flask(__name__)
app.secret_key = "something_else"
bootstrap = Bootstrap(app)

# Flask Parameters
CLIENT_SIDE_URL = "http://127.0.0.1"
PORT = 8080
REDIRECT_URI = "{}:{}/playlists".format(CLIENT_SIDE_URL, PORT)
SCOPE = ("playlist-modify-public playlist-modify-private "
         "playlist-read-collaborative playlist-read-private")

stored_info = {}

class ComparePlaylistForm(FlaskForm):
    choices = SelectMultipleField("Playlists")
    submit = SubmitField("Save")


@app.route("/")
def index():
    sp_oauth = get_oauth()
    return redirect(sp_oauth.get_authorize_url())


@app.route("/playlists")
def display_something():
    #lets display names of playlists
    if request.args.get("code"):
        get_spotify(request.args["code"])
    playlistitems = get_spotify().current_user_playlists()["items"]
    user = get_spotify().current_user()
    stored_info["playlist_names"] = playlistitems
    return render_template("index.html", playlists = playlistitems, user = user)

@app.route("/playlist/analysis/<playlist_id>", methods = ["GET", "POST"])
def analyze_playlist(playlist_id):
    playlistform = ComparePlaylistForm()
    playlistform.choices.choices = [(item["id"], item["name"]) for item in stored_info["playlist_names"]]
    sp = get_spotify()
    if playlist_id in stored_info.keys():
        dic = stored_info[playlist_id][0]

    else:
        playlist = sp.user_playlist(sp.current_user()["id"], playlist_id)
        tracks = playlist["tracks"]
        all_track_info = tracks["items"]
        while tracks["next"]:
            tracks = sp.next(tracks)
            all_track_info.extend(tracks["items"])

        ids = [track["track"]["id"] for track in all_track_info]
        song_df = create_df(ids)
        dic = analyze_dataframe(song_df)
        dic["name"] = playlist["name"]
        dic["image"] = playlist["images"][0]["url"]
        dic["followers"] = playlist["followers"]
        dic["url"] = playlist["external_urls"]["spotify"]
        stored_info[playlist_id] = [song_df, dic]
    if playlistform.validate_on_submit():
        elements = playlistform.choices
        return render_template(playlists = elements)
    return render_template("analysis.html", dictionary= dic, form = playlistform)




def analyze_dataframe(df):
    dic = {}
    dic["tracks"] = [i for i in zip(df["name"], df["artist_name"])]
    dic["danceability"] = np.mean(df["danceability"])
    dic["tempo"] = np.mean(df["tempo"])
    dic["popularity"] = np.mean(df["popularity"])
    dic["loudness"] = np.mean(df["loudness"])
    dic["mode"] = np.mean(df["mode"])
    dic["energy"] = np.mean(df["energy"])
    dic["speechiness"] = np.mean(df["speechiness"])
    dic["acousticness"] = np.mean(df["acousticness"])
    dic["instrumentalness"] = np.mean(df["instrumentalness"])
    dic["liveness"] = np.mean(df["liveness"])
    dic["valence"] = np.mean(df["valence"])
    return dic

def inornah(list, a):
    if a in list:
        return 1
    else:
        return 0

# this function will generate a dataframe in pandas that contains relevant details

def gather_playlist():
    sp = get_spotify()
    playlist_dic = {}
    for item in sp.current_user_playlists()["items"]:
        playlist_dic[item["name"]] = item["uri"][17:]
    return playlist_dic


def create_df(ids):
    sp = get_spotify()
    listsongs = [[
        "id",
        "name",
        "popularity",
        "artist_name",
        "explicit",
        "release date",
        "danceability",
        "energy",
        "loudness",
        "mode",
        "speechiness",
        "acousticness",
        "instrumentalness",
        "liveness",
        "valence",
        "tempo",
        "genres"
    ]]
    def add_songs(b):
        for id in b:
            new_list = []
            track = sp.track(id)
            new_list.append(track["id"])
            new_list.append(track["name"])
            new_list.append(track["popularity"])
            new_list.append(track["artists"][0]["name"])
            new_list.append(track["explicit"])
            new_list.append(track["album"]["release_date"])
            audio_features = sp.audio_features(track["id"])[0]
            new_list.append(audio_features["danceability"])
            new_list.append(audio_features["energy"])
            new_list.append(audio_features["loudness"])
            new_list.append(audio_features["mode"])
            new_list.append(audio_features["speechiness"])
            new_list.append(audio_features["acousticness"])
            new_list.append(audio_features["instrumentalness"])
            new_list.append(audio_features["liveness"])
            new_list.append(audio_features["valence"])
            new_list.append(audio_features["tempo"])
            new_list.append(sp.artist(track["artists"][0]["uri"])["genres"])
            listsongs.append(new_list)
    add_songs(ids)
    song_df = pd.DataFrame(data=listsongs[1:], columns=listsongs[0])
    all_genres = []
    for item in song_df["genres"]:
        for value in item:
            if value not in all_genres:
                all_genres.append(value)
    for a in all_genres:
        song_df[a] = [inornah(x, a) for x in song_df["genres"]]
    return song_df


# the next three functions are meant to help with getting the spotify information
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

#this just runs the function
if __name__ == "__main__":
    app.run(debug=True, port=PORT)