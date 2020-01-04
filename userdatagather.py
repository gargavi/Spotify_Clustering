import spotipy
import spotipy.util as util
import time
import pymysql as psql
import sqlalchemy as alch
from sqlalchemy.types import VARCHAR
import winsound
import pandas as pd
from spotipy.oauth2 import SpotifyClientCredentials


frequency = 2500  # Set Frequency To 2500 Hertz
duration = 1000  # Set Duration To 1000 ms == 1 second


t_start = time.time()
username = "12123404397"
CLIENT_ID = 'f48bed994e9a4ab9a939688387022cb2'
CLIENT_SECRET = '4a31ad0a2e5540e6a8b0486cc2915ffe'
redirect_uri = 'http://localhost:8888/callback/'

scope = 'user-library-read'


#this function generates a Spotipy Instance via the token method
def generate_host():
    token = util.prompt_for_user_token(username, scope, CLIENT_ID, CLIENT_SECRET, redirect_uri)
    if token:
        sp = spotipy.Spotify(auth=token)
        print('Generated a Spotify Class Instance')
    else:
        raise ValueError('enter valid credentials')
    return sp

client_credentials_manager = SpotifyClientCredentials(CLIENT_ID, CLIENT_SECRET)

#this method generates a Spotipy Instance using a client credentials method -> Doesn't allow user specific access

sp = generate_host()

listsongs = [[
    "id",
    "name",
    "popularity",
    "explicit",
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
b = sp.current_user_saved_tracks(limit= 40)
for i in range(100):
    b = sp.current_user_saved_tracks(limit = 40, offset = 40*i)


def add_songs(b):
    for song in b["items"]:
        new_list = []
        new_list.append(song["track"]["id"])
        new_list.append(song["track"]["name"])
        temp = sp.track(song["track"]["id"])
        new_list.append(temp["popularity"])
        new_list.append(temp["artists"][0]["name"])
        new_list.append(temp["explicit"])
        audio_features = sp.audio_features(song["track"]["id"])[0]
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
        new_list.append(sp.artist(temp["artists"][0]["uri"])["genres"])
        listsongs.append(new_list)


import csv
with open("output.csv", "w", newline="") as totalsongs:
    writer = csv.writer(totalsongs)
    writer.writerows(listsongs)