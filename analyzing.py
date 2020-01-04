#this is to analyze the various playlists that I have
import pandas as pd
import numpy as np

song_df = pd.read_csv("output.csv",encoding = "cp1252" )
mapping_df = pd.read_csv("mapping.csv")
mapping_df = mapping_df[["name", "number"]]


all_mean = []
all_count = []

for index, row in mapping_df.iterrows():
    playlist_df = pd.read_csv("playlist_" + str(row["number"]) + ".csv")
    print(row["name"])
    temp = pd.Series(data = {"Count" : playlist_df.shape[0]})
    total = playlist_df.mean().append(temp)
    all_mean.append(total)
    all_count.append(playlist_df.sum())

pd.concat(all_mean, axis = 1).to_csv("means.csv")
pd.concat(all_count, axis = 1).to_csv("counts.csv")

