import pandas as pd
from flask import Flask, redirect, request, render_template, session, url_for
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import SelectMultipleField, SubmitField, BooleanField, StringField, validators
from wtforms.validators import NoneOf, Required
from io import BytesIO
import base64
import seaborn as sns
sns.set()
from sklearn.linear_model import LinearRegression

import numpy as np
import matplotlib.pyplot as plt
import spotipy
import spotipy.oauth2


application = Flask(__name__)
application.secret_key = "something_else"
bootstrap = Bootstrap(application)

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


class DivideForm(FlaskForm):
    first= SelectMultipleField("Songs in First Playlist")
    second = SelectMultipleField("Songs in Second Playlist")
    submit = SubmitField("Save")

class RenameForm(FlaskForm):
    newname = StringField("New Name?", [validators.required()])
    submit = SubmitField("Rename")

class SavePlaylistForm(FlaskForm):
    savefirst = BooleanField("Save First Playlist?")
    namefirst = StringField("Name of the Playlist?")
    savesecond = BooleanField("Save Second Playlist?")
    namesecond = StringField("Name of the Playlist?")
    submit2 = SubmitField("Confirm?")

    def __init__(self, playlist_names):
        super(SavePlaylistForm, self).__init__()
        self.namefirst.validators.append(
            NoneOf(playlist_names, message="That name is already in use!"))
        self.namesecond.validators.append(NoneOf(
            playlist_names, message = "That name is already in use!"))
        self.namesecond.validators.append(NoneOf([self.namefirst.data], message = "Can't have same name"))


@application.route("/")
def index():
    sp_oauth = get_oauth()
    return redirect(sp_oauth.get_authorize_url())


@application.route("/playlists", methods = ["GET", "POST"])
def display_something():
    #lets display names of playlists
    if request.args.get("code"):
        get_spotify(request.args["code"])
    playlistitems = get_spotify().current_user_playlists()["items"]
    user = get_spotify().current_user()
    stored_info["playlist_names"] = playlistitems
    return render_template("index.html", playlists = playlistitems, user = user)

@application.route("/rename/<playlist_id>", methods = ["GET", "POST"])
def rename_playlist(playlist_id):
    sp = get_spotify()
    renameform = RenameForm()
    if renameform.is_submitted() and renameform.validate():
        name = renameform.newname.data
        sp.user_playlist_change_details(sp.current_user()["id"], playlist_id, name = name)
        return redirect(url_for("display_something"))
    return render_template("rename.html", form = renameform)


@application.route("/addsongs")
def add_songs():
    sp = get_spotify()
    sp.current_user_saved_tracks(limit= 35)



@application.route("/playlist/analysis/<playlist_id>", methods = ["GET", "POST"])
def analyze_playlist(playlist_id):
    playlistform = ComparePlaylistForm()
    playlistform.choices.choices = [(item["id"], item["name"]) for item in stored_info["playlist_names"]]
    sp = get_spotify()
    if playlist_id in stored_info.keys():
        dic = stored_info[playlist_id][1]

    else:
        playlist = sp.user_playlist(sp.current_user()["id"], playlist_id)
        tracks = playlist["tracks"]
        all_track_info = tracks["items"]
        while tracks["next"]:
            tracks = sp.next(tracks)
            all_track_info.extend(tracks["items"])
        ids = [track["track"]["id"] for track in all_track_info if track["track"]["id"] != None]
        song_df = create_df(ids)
        dic = analyze_dataframe(song_df)
        dic["id"] = playlist_id
        dic["name"] = playlist["name"]
        dic["image"] = playlist["images"][0]["url"]
        dic["followers"] = playlist["followers"]
        dic["url"] = playlist["external_urls"]["spotify"]
        stored_info[playlist_id] = [song_df, dic]
    if playlistform.is_submitted():
        elements = playlistform.choices.data
        return render_template("comparison.html", playlists= elements)
    return render_template("analysis.html", dictionary= dic, form = playlistform)


@application.route("/playlist/furtheranalysis/<word>/<playlist_id>")
def analyze_danceability(word, playlist_id):
    if playlist_id in stored_info.keys():
        song_df = stored_info[playlist_id][0]
        dic = stored_info[playlist_id][1]
    else:
        sp = get_spotify()
        playlist = sp.user_playlist(sp.current_user()["id"], playlist_id)
        tracks = playlist["tracks"]
        all_track_info = tracks["items"]
        while tracks["next"]:
            tracks = sp.next(tracks)
            all_track_info.extend(tracks["items"])
        ids = [track["track"]["id"] for track in all_track_info]
        song_df = create_df(ids)
        dic = analyze_dataframe(song_df)
        dic["id"] = playlist_id
        dic["name"] = playlist["name"]
        dic["image"] = playlist["images"][0]["url"]
        dic["followers"] = playlist["followers"]
        dic["url"] = playlist["external_urls"]["spotify"]
        stored_info[playlist_id] = [song_df, dic]
    song_df.index += 1
    all_images = []
    elements = dic["tracks"]
    for i in range(len(song_df.index)//20 + 1) :
        series = song_df[word][20*i : 20*(i+1)]
        series.plot.bar(legend = False)
        figure = plt.gcf()
        tmpfile = BytesIO()
        figure.savefig(tmpfile, format='png')
        encoded = base64.b64encode(tmpfile.getvalue()).decode('utf-8')
        all_images.append(encoded)
    return render_template("furtheranalysis.html", name = word, image = all_images, elements = elements )

@application.route("/playlist/divide/<playlist_id>", methods = ["GET", "POST"])
def divide_playlist(playlist_id):
    if playlist_id in stored_info.keys():
        song_df = stored_info[playlist_id][0]
        dic = stored_info[playlist_id][1]
    else:
        sp = get_spotify()
        playlist = sp.user_playlist(sp.current_user()["id"], playlist_id)
        tracks = playlist["tracks"]
        all_track_info = tracks["items"]
        while tracks["next"]:
            tracks = sp.next(tracks)
            all_track_info.extend(tracks["items"])
        ids = [track["track"]["id"] for track in all_track_info]
        song_df = create_df(ids)
        dic = analyze_dataframe(song_df)
        dic["id"] = playlist_id
        dic["name"] = playlist["name"]
        dic["image"] = playlist["images"][0]["url"]
        dic["followers"] = playlist["followers"]
        dic["url"] = playlist["external_urls"]["spotify"]
        stored_info[playlist_id] = [song_df, dic]
    form = DivideForm()
    form.first.choices = [i for i in zip(song_df["id"], song_df["name"])]
    form.second.choices = [i for i in zip(song_df["id"], song_df["name"])]
    if form.is_submitted():
        session["first"] = form.first.data
        session["second"] = form.second.data
        return redirect(url_for("divide_two", playlist_id = playlist_id))

    return render_template("division.html", form = form)


@application.route("/playlist/divide/two/<playlist_id>", methods = ["GET", "POST"])
def divide_two(playlist_id):
    song_df = stored_info[playlist_id][0]
    if "label" in song_df.columns:
        song_df = song_df.drop("label", axis = 1)
    first = session["first"]
    second = session["second"]
    first_df = song_df[song_df["id"].isin(first)]
    second_df = song_df[song_df["id"].isin(second)]
    first_df["label"] = 1
    second_df["label"] = 0
    predict = pd.concat([first_df, second_df])
    predict = predict.select_dtypes(exclude=["object"])
    features = predict[[i for i in predict.columns if i != "label"]]
    linear = LinearRegression().fit(features, predict["label"])
    prediction = linear.predict(song_df.select_dtypes(exclude=["object"]))
    song_df["label"] = prediction
    first_playlist = song_df[song_df["label"] > .4]
    second_playlist = song_df[song_df["label"] < .6]
    first = [item for item in zip(first_playlist["name"], first_playlist["artist_name"])]
    second = [item for item in zip(second_playlist["name"], second_playlist["artist_name"])]
    playlist_names = [i["name"] for i in stored_info["playlist_names"]]
    playlistform = SavePlaylistForm(playlist_names=playlist_names)
    if playlistform.is_submitted() and playlistform.validate():
        sp = get_spotify()
        if playlistform.savefirst.data:
            sp.user_playlist_create(sp.current_user()["id"], playlistform.namefirst.data)
            firstid = get_playlist_id_by_name(playlistform.namefirst.data)
            songs = first_playlist["id"]
            for i in range(len(songs) // 100 + 1):
                sp.user_playlist_add_tracks(sp.current_user()["id"], firstid, songs[100*i: 100 * (i + 1)])
        if playlistform.savesecond.data:
            sp.user_playlist_create(sp.current_user()["id"], playlistform.namesecond.data)
            secondid = get_playlist_id_by_name(playlistform.namesecond.data)
            songs = second_playlist["id"]
            for i in range(len(songs) // 100 + 1):
                sp.user_playlist_add_tracks(sp.current_user()["id"], secondid, songs[100*i: 100 * (i + 1)])
        if playlistform.savefirst.data and playlistform.savesecond.data:
            firstplaylist = sp.user_playlist(sp.current_user()["id"], firstid)
            secondplaylist = sp.user_playlist(sp.current_user()["id"], secondid)
            return render_template("newplaylists.html", first = firstplaylist, second = secondplaylist)
        elif playlistform.savefirst.data:
            firstplaylist = sp.user_playlist(sp.current_user()["id"], firstid)
            return render_template("newplaylists.html", first=firstplaylist, second=None)
        elif playlistform.savesecond.data:
            secondplaylist = sp.user_playlist(sp.current_user()["id"], secondid)
            return render_template("newplaylists.html", first= None, second=secondplaylist)
        else:
            return render_template("newplaylist.html", first = None, second = None)
    return render_template("twoplaylists.html", first=first, second=second, form=playlistform)


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



def get_user_playlists():
    """Return an id, name, images tuple of a user's playlists."""
    spotify = get_spotify()
    user_id = spotify.current_user()["id"]
    results = spotify.user_playlists(user_id)

    playlists = results["items"]
    while results["next"]:
        results = spotify.next(results)
        playlists.extend(results["items"])

    playlist_names = [{"id": playlist["id"], "name": playlist["name"],
                       "images": playlist["images"]} for playlist in playlists]
    return playlist_names


def get_playlist_id_by_name(name):
    """Return the id for a playlist with name: 'name'."""
    return [playlist["id"] for playlist in get_user_playlists() if
            playlist["name"] == name][0]

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
    application.run(debug=True, port=PORT)