import datetime as dt
import json
import math
from pathlib import Path
import sys
from time import sleep

import imageio.v3 as iio
import mysql.connector
import numpy as np
import requests
import streamlink
from streamlink.plugins.twitch import __plugin__ as Twitch, TwitchM3U8Parser
from streamlink.stream.hls.m3u8 import parse_m3u8 as load_hls_playlist

RELOAD_TIME = 4
DISTANCE_CUTOFF = 10000

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

sql_add_time = "INSERT INTO times (id_date, id_streamer, game_time, real_time) VALUES (%s, %s, %s, %s)"

if len(sys.argv) < 2:
    raise Exception("No streamer argument supplied")
streamer_name = sys.argv[1]

# Figure out placement depending on streamer
gametime_trim_top = 0
gametime_trim_bottom = 0
realtime_trim_top = 0
realtime_trim_bottom = 0
gametime_gap = 0
realtime_gap = 0
if streamer_name == "forsen":
    gametime_x = 1700
    gametime_y = 80
    gametime_scale = 4
    realtime_x = 1700
    realtime_y = 32
    realtime_scale = 4
elif streamer_name.startswith("xqc"):
    gametime_x = 0
    gametime_y = 681
    gametime_scale = 8
    gametime_gap = 1
    gametime_trim_top = 1
    gametime_trim_bottom = 1
    realtime_x = 11
    realtime_y = 648
    realtime_scale = 3.5
    realtime_gap = 0.5
    realtime_trim_bottom = 1

def nearest_neighbour_fractional(img, scale):
    in_h, in_w = img.shape
    out_h = int(round(in_h * scale))
    out_w = int(round(in_w * scale))
    
    # Compute source indices (nearest neighbor)
    src_y = np.floor(np.arange(out_h) / scale).astype(int)
    src_x = np.floor(np.arange(out_w) / scale).astype(int)
    
    # Clip to valid range
    src_y = np.clip(src_y, 0, in_h - 1)
    src_x = np.clip(src_x, 0, in_w - 1)
    
    # Generate output by indexing
    out = img[src_y[:, None], src_x[None, :]]
    return out

digit_pixelmap_gametime = np.array([
    nearest_neighbour_fractional(digit[gametime_trim_top : digit.shape[0] - gametime_trim_bottom, :], gametime_scale)
    for digit in digit_pixelmap
])
digit_pixelmap_realtime = np.array([
    nearest_neighbour_fractional(digit[realtime_trim_top : digit.shape[0] - realtime_trim_bottom, :], realtime_scale)
    for digit in digit_pixelmap
])

with open(Path(__file__).parent.joinpath("secrets.json")) as secret_json_file:
    json_data = json.load(secret_json_file)
    rw_db_pw = json_data["database_rw_pw"]

def compare_image_to_pixelmap(image, pixelmap, colour):
    diff = np.square(image.astype(np.float32) - colour)
    mask = np.broadcast_to(pixelmap[..., np.newaxis], diff.shape) # 1D array
    diff = diff[mask] # Turns diff into 1D array
    ssd = np.sum(diff)
    return ssd

def get_image_from_frame(index, frame, width, scale, gap):
    scale_bonus = 0
    gap_bonus = 0
    if (index >= 2):
        scale_bonus += 2
        gap_bonus += 1
    if (index >= 4):
        scale_bonus += 2
        gap_bonus += 1
    x = math.floor((((7 * index) + scale_bonus - index) * scale) + ((index + gap_bonus) * gap))
    image = frame[:, x:x+width, :]
    return image

def get_time_from_frame(frame, colour, scale, gap, pixelmap, debug=False):
    images = [get_image_from_frame(idx, frame, pixelmap.shape[2], scale, gap) for idx in range(7)]
    # images = [frame[:,0:7*scale,:], frame[:,6*scale+(1*gap):13*scale+(1*gap),:], frame[:,14*scale+(3*gap):21*scale+(3*gap),:], frame[:,20*scale+(4*gap):27*scale+(4*gap),:], frame[:,28*scale+(6*gap):35*scale+(6*gap),:], frame[:,34*scale+(7*gap):41*scale+(7*gap),:], frame[:,40*scale+(8*gap):47*scale+(8*gap),:]]
    image_place_value = [600000, 60000, 10000, 1000, 100, 10, 1]

    worst_best_distance = 0
    milliseconds = 0
    for idx_image, image in enumerate(images):
        # Find most likely digit. If it's a close enough match, continue. If not, return None
        best_num = 0
        best_distance = float("inf")
        for idx_pm, pm in enumerate(pixelmap):
            colour_distance = compare_image_to_pixelmap(image, pm == 'c', colour)
            black_distance = compare_image_to_pixelmap(image, pm == 'b', (0,0,0))
            total_distance = (colour_distance + black_distance) / np.count_nonzero(pm != 't')
            if total_distance < best_distance:
                best_distance = total_distance
                best_num = idx_pm

        if best_distance > DISTANCE_CUTOFF:
            print(f"Best distance too high: {best_distance}")
            return None
        milliseconds += best_num * image_place_value[idx_image]
        if best_distance > worst_best_distance:
            worst_best_distance = best_distance
    
    if (debug):
        print(str((str(dt.timedelta(milliseconds=milliseconds)), worst_best_distance)))

    return dt.timedelta(milliseconds=milliseconds)

def main_loop():
    session = streamlink.Streamlink(options={"webbrowser-headless": True})
    if streamer_name == "xqc_kick":
        response = requests.get("https://piggeywig2000.dev/kickm3u8/xqc")
        if response.status_code != 200:
            raise Exception(f"Kick stream link not found: {response.status_code} - {response.text}")
        m3u8_link = response.text.strip()
        if len(m3u8_link) == 0:
            raise Exception(f"{streamer_name} not live")
        streams = session.streams(m3u8_link)
        stream = streams["live"]
    else:
        plugin = Twitch(session, f"https://www.twitch.tv/{streamer_name}", options={"low-latency": True, "disable-ads": True, "api_header": {"Client-ID": "ue6666qo983tsx6so1t0vnawi233wa"}})
        streams = plugin.streams()
        if "1080p60" not in streams:
            raise Exception(f"{streamer_name} not live")
        stream = streams["1080p60"]
    
    start_time = dt.datetime.now(dt.UTC)
    iterations = 0
    while True:
        target_time = start_time + dt.timedelta(seconds=RELOAD_TIME*iterations)
        sleep_time = target_time - dt.datetime.now(dt.UTC)
        if sleep_time <= dt.timedelta():
            print("Reload overdue, not sleeping...")
            start_time = dt.datetime.now(dt.UTC)
            iterations = 0
        else:
            print(f"Sleeping for {sleep_time.total_seconds()}")
            sleep(sleep_time.total_seconds())
        iterations += 1

        m3u8_response = requests.get(stream.url).text
        m3u8_playlist = load_hls_playlist(m3u8_response, parser=TwitchM3U8Parser)
        latest_segment = m3u8_playlist.segments[-1]
        if latest_segment.ad:
            print("Has ad, skipping...")
            continue
        segment_data = requests.get(latest_segment.uri).content
        # meta = iio.immeta(segment_data, index=None, extension=".ts")
        # last_frame_idx = round(meta["duration"] * meta["fps"]) - 1
        last_frame = iio.imread(segment_data, index=0, extension=".ts")

        # last_frame = iio.imread("screenshot.png")

        game_time = get_time_from_frame(last_frame[gametime_y:gametime_y+(digit_pixelmap_gametime.shape[1]),gametime_x:math.floor(gametime_x+(47*gametime_scale)+(8*gametime_gap)),:], (255, 255, 85), gametime_scale, gametime_gap, digit_pixelmap_gametime, True)
        real_time = get_time_from_frame(last_frame[realtime_y:realtime_y+(digit_pixelmap_realtime.shape[1]),realtime_x:math.floor(realtime_x+(47*realtime_scale)+(8*realtime_gap)),:], (85, 255, 255), realtime_scale, realtime_gap, digit_pixelmap_realtime, True)
        if game_time == None or real_time == None:
            continue
        
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