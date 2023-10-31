import datetime as dt
import json
from pathlib import Path
import sys
from time import sleep

import imageio.v3 as iio
import mysql.connector
import numpy as np
import requests
import streamlink
from streamlink.plugins.twitch import TwitchM3U8Parser, TwitchM3U8
from streamlink.stream.hls_playlist import load as load_hls_playlist

RELOAD_TIME = 4
DISTANCE_CUTOFF = 150

digit_pixelmap = np.array([
    [['t', 'b', 'b', 'b', 'b', 'b', 't'],
     ['b', 'b', 'c', 'c', 'c', 'b', 'b'],
     ['b', 'c', 'b', 'b', 'b', 'c', 'b'],
     ['b', 'c', 'b', 'b', 'c', 'c', 'b'],
     ['b', 'c', 'b', 'c', 'b', 'c', 'b'],
     ['b', 'c', 'c', 'b', 'b', 'c', 'b'],
     ['b', 'c', 'b', 'b', 'b', 'c', 'b'],
     ['b', 'b', 'c', 'c', 'c', 'b', 'b'],
     ['t', 'b', 'b', 'b', 'b', 'b', 't'],],

    [['t', 't', 'b', 'b', 'b', 't', 't'],
     ['t', 'b', 'b', 'c', 'b', 't', 't'],
     ['t', 'b', 'c', 'c', 'b', 't', 't'],
     ['t', 'b', 'b', 'c', 'b', 't', 't'],
     ['t', 't', 'b', 'c', 'b', 't', 't'],
     ['t', 't', 'b', 'c', 'b', 't', 't'],
     ['b', 'b', 'b', 'c', 'b', 'b', 'b'],
     ['b', 'c', 'c', 'c', 'c', 'c', 'b'],
     ['b', 'b', 'b', 'b', 'b', 'b', 'b'],],

    [['t', 'b', 'b', 'b', 'b', 'b', 't'],
     ['b', 'b', 'c', 'c', 'c', 'b', 'b'],
     ['b', 'c', 'b', 'b', 'b', 'c', 'b'],
     ['b', 'b', 'b', 'b', 'b', 'c', 'b'],
     ['t', 'b', 'b', 'c', 'c', 'b', 'b'],
     ['b', 'b', 'c', 'b', 'b', 'b', 'b'],
     ['b', 'c', 'b', 'b', 'b', 'c', 'b'],
     ['b', 'c', 'c', 'c', 'c', 'c', 'b'],
     ['b', 'b', 'b', 'b', 'b', 'b', 'b'],],

    [['t', 'b', 'b', 'b', 'b', 'b', 't'],
     ['b', 'b', 'c', 'c', 'c', 'b', 'b'],
     ['b', 'c', 'b', 'b', 'b', 'c', 'b'],
     ['b', 'b', 'b', 'b', 'b', 'c', 'b'],
     ['t', 't', 'b', 'c', 'c', 'b', 'b'],
     ['b', 'b', 'b', 'b', 'b', 'c', 'b'],
     ['b', 'c', 'b', 'b', 'b', 'c', 'b'],
     ['b', 'b', 'c', 'c', 'c', 'b', 'b'],
     ['t', 'b', 'b', 'b', 'b', 'b', 't'],],

    [['t', 't', 't', 'b', 'b', 'b', 'b'],
     ['t', 't', 'b', 'b', 'c', 'c', 'b'],
     ['t', 'b', 'b', 'c', 'b', 'c', 'b'],
     ['b', 'b', 'c', 'b', 'b', 'c', 'b'],
     ['b', 'c', 'b', 'b', 'b', 'c', 'b'],
     ['b', 'c', 'c', 'c', 'c', 'c', 'b'],
     ['b', 'b', 'b', 'b', 'b', 'c', 'b'],
     ['t', 't', 't', 't', 'b', 'c', 'b'],
     ['t', 't', 't', 't', 'b', 'b', 'b'],],

    [['b', 'b', 'b', 'b', 'b', 'b', 'b'],
     ['b', 'c', 'c', 'c', 'c', 'c', 'b'],
     ['b', 'c', 'b', 'b', 'b', 'b', 'b'],
     ['b', 'c', 'c', 'c', 'c', 'b', 'b'],
     ['b', 'b', 'b', 'b', 'b', 'c', 'b'],
     ['b', 'b', 'b', 't', 'b', 'c', 'b'],
     ['b', 'c', 'b', 'b', 'b', 'c', 'b'],
     ['b', 'b', 'c', 'c', 'c', 'b', 'b'],
     ['t', 'b', 'b', 'b', 'b', 'b', 't'],],

    [['t', 't', 'b', 'b', 'b', 'b', 't'],
     ['t', 'b', 'b', 'c', 'c', 'b', 't'],
     ['b', 'b', 'c', 'b', 'b', 'b', 't'],
     ['b', 'c', 'b', 'b', 'b', 'b', 't'],
     ['b', 'c', 'c', 'c', 'c', 'b', 'b'],
     ['b', 'c', 'b', 'b', 'b', 'c', 'b'],
     ['b', 'c', 'b', 'b', 'b', 'c', 'b'],
     ['b', 'b', 'c', 'c', 'c', 'b', 'b'],
     ['t', 'b', 'b', 'b', 'b', 'b', 't'],],

    [['b', 'b', 'b', 'b', 'b', 'b', 'b'],
     ['b', 'c', 'c', 'c', 'c', 'c', 'b'],
     ['b', 'c', 'b', 'b', 'b', 'c', 'b'],
     ['b', 'b', 'b', 'b', 'b', 'c', 'b'],
     ['t', 't', 'b', 'b', 'c', 'b', 'b'],
     ['t', 't', 'b', 'c', 'b', 'b', 't'],
     ['t', 't', 'b', 'c', 'b', 't', 't'],
     ['t', 't', 'b', 'c', 'b', 't', 't'],
     ['t', 't', 'b', 'b', 'b', 't', 't'],],

    [['t', 'b', 'b', 'b', 'b', 'b', 't'],
     ['b', 'b', 'c', 'c', 'c', 'b', 'b'],
     ['b', 'c', 'b', 'b', 'b', 'c', 'b'],
     ['b', 'c', 'b', 'b', 'b', 'c', 'b'],
     ['b', 'b', 'c', 'c', 'c', 'b', 'b'],
     ['b', 'c', 'b', 'b', 'b', 'c', 'b'],
     ['b', 'c', 'b', 'b', 'b', 'c', 'b'],
     ['b', 'b', 'c', 'c', 'c', 'b', 'b'],
     ['t', 'b', 'b', 'b', 'b', 'b', 't'],],

    [['t', 'b', 'b', 'b', 'b', 'b', 't'],
     ['b', 'b', 'c', 'c', 'c', 'b', 'b'],
     ['b', 'c', 'b', 'b', 'b', 'c', 'b'],
     ['b', 'c', 'b', 'b', 'b', 'c', 'b'],
     ['b', 'b', 'c', 'c', 'c', 'c', 'b'],
     ['t', 'b', 'b', 'b', 'b', 'c', 'b'],
     ['t', 'b', 'b', 'b', 'c', 'b', 'b'],
     ['t', 'b', 'c', 'c', 'b', 'b', 't'],
     ['t', 'b', 'b', 'b', 'b', 't', 't'],],
])
digit_pixelmap = np.repeat(np.repeat(digit_pixelmap, 3, axis=1), 3, axis=2)

sql_add_time = "INSERT INTO times (id_date, id_streamer, game_time, real_time) VALUES (%s, %s, %s, %s)"

if len(sys.argv) < 2:
    raise Exception("No streamer argument supplied")
streamer_name = sys.argv[1]

with open(Path(__file__).parent.joinpath("secrets.json")) as secret_json_file:
    rw_db_pw = json.load(secret_json_file)["database_rw_pw"]

def compare_image_to_pixelmap(image, pixelmap, colour):
    count = np.count_nonzero(pixelmap)
    if count == 0:
        return 0
    diff = image - colour
    dist = np.linalg.norm(diff, axis=2) * pixelmap
    total = np.sum(dist / count)
    return total

def get_time_from_frame(frame, colour, debug=False):
    images = [frame[:,0:21,:], frame[:,18:39,:], frame[:,42:63,:], frame[:,60:81,:], frame[:,84:105,:], frame[:,102:123,:], frame[:,120:141,:]]
    image_place_value = [600000, 60000, 10000, 1000, 100, 10, 1]

    milliseconds = 0
    for idx_image, image in enumerate(images):
        #Find most likely digit. If it's a close enough match, continue. If not, return None
        best_num = 0
        best_distance = float("inf")
        best_colour_distance = 0
        best_black_distance = 0
        for idx_pm, pm in enumerate(digit_pixelmap):
            colour_distance = compare_image_to_pixelmap(image, pm == 'c', colour)
            black_distance = compare_image_to_pixelmap(image, pm == 'b', (0,0,0))
            total_distance = colour_distance + black_distance
            if total_distance < best_distance:
                best_distance = total_distance
                best_colour_distance = colour_distance
                best_black_distance = black_distance
                best_num = idx_pm

        if best_distance > DISTANCE_CUTOFF:
            return None
        milliseconds += best_num * image_place_value[idx_image]
    
    if (debug):
        print(str((str(dt.timedelta(milliseconds=milliseconds)), best_distance, best_colour_distance, best_black_distance)))

    return dt.timedelta(milliseconds=milliseconds)

def main_loop():
    session = streamlink.Streamlink()
    options = streamlink.options.Options()
    if streamer_name == "xqc_kick":
        #Hardcode xqc's kick M3U8 URL
        streams = session.streams("https://kurl.co/29f11")
    else:
        options.set("low-latency", True)
        options.set("disable-ads", True)
        options.set("api-header", {"Client-ID": "ue6666qo983tsx6so1t0vnawi233wa"})
        streams = session.streams(f"https://www.twitch.tv/{streamer_name}", options)
    if "1080p60" not in streams:
        raise Exception(f"{streamer_name} not live")
    stream = streams["1080p60"]
    
    start_time = dt.datetime.utcnow()
    iterations = 0
    while True:
        target_time = start_time + dt.timedelta(seconds=RELOAD_TIME*iterations)
        sleep_time = target_time - dt.datetime.utcnow()
        if sleep_time <= dt.timedelta():
            print("Reload overdue, not sleeping...")
            start_time = dt.datetime.utcnow()
            iterations = 0
        else:
            print(f"Sleeping for {sleep_time.total_seconds()}")
            sleep(sleep_time.total_seconds())
        iterations += 1

        m3u8_response = requests.get(stream.url).text
        m3u8_playlist = load_hls_playlist(m3u8_response, parser=TwitchM3U8Parser, m3u8=TwitchM3U8)
        latest_segment = m3u8_playlist.segments[-1]
        if latest_segment.ad:
            print("Has ad, skipping...")
            continue
        segment_data = requests.get(latest_segment.uri).content
        # meta = iio.immeta(segment_data, index=None, extension=".ts")
        # last_frame_idx = round(meta["duration"] * meta["fps"]) - 1
        last_frame = iio.imread(segment_data, index=0, extension=".ts")

        game_time = get_time_from_frame(last_frame[81:108,1749:1890,:], (255, 255, 85), True)
        real_time = get_time_from_frame(last_frame[33:60,1749:1890,:], (85, 255, 255))
        if game_time == None:
            continue
        #If real time is covered, just use game time
        #This is workaround because of xQc's TTS muted icon
        if real_time == None:
            real_time = game_time
        
        cnx_rw = mysql.connector.connect(user='forsen_minecraft_rw', password=rw_db_pw, host='127.0.0.1', database='forsen_minecraft')
        try:
            cursor = cnx_rw.cursor()
            cursor.execute(sql_add_time, (latest_segment.date, streamer_name.replace("_kick", ""), game_time, real_time))
            cursor.close()
            cnx_rw.commit()
        finally:
            cnx_rw.close()

def thread_entry_point():
    while True:
        try:
            main_loop()
        except Exception as e:
            if str(e) != f"{streamer_name} not live" and "404 Client Error" not in str(e):
                print("Error in thread: " + str(e))
        sleep(10)

thread_entry_point()