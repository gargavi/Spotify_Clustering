import spotipy
import spotipy.util as util
import time
import winsound
import csv
import pandas as pd
import numpy as np
from spotipy.oauth2 import SpotifyClientCredentials


frequency = 2500  # Set Frequency To 2500 Hertz
duration = 1000  # Set Duration To 1000 ms == 1 second


t_start = time.time()
username = "12123404397"
CLIENT_ID = 'f48bed994e9a4ab9a939688387022cb2'
CLIENT_SECRET = '4a31ad0a2e5540e6a8b0486cc2915ffe'
redirect_uri = 'http://localhost:8888/callback/'

scope = 'user-library-read user-library-modify'

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

print(sp.track("3YU6vJbjYUG0tiJyXf9x5V"))
def gather_library(number):
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
        for song in b["items"]:
            new_list = []
            new_list.append(song["track"]["id"])
            new_list.append(song["track"]["name"])
            temp = sp.track(song["track"]["id"])
            new_list.append(temp["popularity"])
            new_list.append(temp["artists"][0]["name"])
            new_list.append(temp["explicit"])
            new_list.append(temp["album"]["release_date"])
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
    for i in range(number // 40):
        try:
            b = sp.current_user_saved_tracks(limit=40, offset=40 * i)
            add_songs(b)
            print(40 * i, " songs done")
        except Exception as e:
            print(e)
            break
    return listsongs

def gather_playlist():
    playlist_dic = {}
    for item in sp.current_user_playlists()["items"]:
        playlist_dic[item["name"]] = item["uri"][17:]
    return playlist_dic


def add_songs(playlist_id):
    tracks = sp.user_playlist(sp.current_user()["id"], playlist_id)["tracks"]
    for item in tracks["items"]:
        if item["track"]["id"] != None and not sp.current_user_saved_tracks_contains([item["track"]["id"]])[0]:
            print(item["track"]["name"])


def dummy_genre(song_df):
    all_genres = []
    for item in song_df["genres"]:
        item = item[1:-1]
        item = item.split(",")
        for element in item:
            element = element.strip()
            element = element[1: -1]
            if element not in all_genres:
                all_genres.append(element)
    for a in all_genres:
        values = []
        for item in song_df["genres"]:
            item = item[1:-1]
            item = item.split(",")
            b = lambda x: x.strip()[1:-1]
            item = [b(y) for y in item]
            if a in item:
                values.append(1)
            else:
                values.append(0)
        song_df[a] = values




def inornah(list, a):
    if a in list:
        return 1
    else:
        return 0

def song_dataframe(number, rewrite):
    if rewrite:
        listsongs = gather_library(number)
        song_df = pd.DataFrame(data = listsongs[1:], columns = listsongs[0])
        all_genres = []
        for item in song_df["genres"]:
            for value in item:
                if value not in all_genres:
                    all_genres.append(value)
        for a in all_genres:
            song_df[a] = [inornah(x, a) for x in song_df["genres"]]
        song_df.to_csv("output.csv")
        return song_df
    else:
        return pd.read_csv("output.csv",encoding = "cp1252" )



input()
song_df = song_dataframe(2500, False)


#
#new goal is to analyze the playlists themselves

playlist_dic = gather_playlist()

mapping_dic = {"number" : [], "name": []}
number = 0
for key, value in playlist_dic.items():
    all_items = []
    max = True
    while (max):
        tracks = sp.user_playlist_tracks(sp.current_user()["id"], value , limit = 100, offset = len(all_items))
        for item in tracks["items"]:
            all_items.append(item)
        if len(tracks["items"]) < 100:
            max = False
    relevant_ids = []
    for item in all_items:
        relevant_ids.append(item["track"]["id"])
    playlist_df = song_df[song_df["id"].isin(relevant_ids)]
    print(key, playlist_df.shape)
    playlist_df.to_csv("playlist_" + str(number) + ".csv")
    mapping_dic["number"].append(number)
    mapping_dic["name"].append(key)
    number += 1

pd.DataFrame.from_dict(mapping_dic).to_csv("mapping.csv")


#lots left to do, but we can do a lot of work with this; very excited to work on this project
    #do preliminary analysis and such in jupyter but we can work with flask framework to add
    #a variety of functionality and exploration features

p