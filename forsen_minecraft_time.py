import datetime as dt
from flask import Flask, request, g
from flask_cors import CORS
import json
import mysql.connector
from pathlib import Path

sql_get_latest_time = "SELECT id_date, game_time, real_time FROM times WHERE id_streamer = %s ORDER BY id_date DESC LIMIT 1"
sql_get_time_history = "SELECT id_date, game_time, real_time FROM times WHERE id_date >= %s AND id_date < %s AND id_streamer = %s ORDER BY id_date DESC"

app = Flask("forsen_minecraft_time")
CORS(app)

with open(Path(__file__).parent.joinpath("secrets.json")) as secret_json_file:
    r_db_pw = json.load(secret_json_file)["database_r_pw"]

def get_db():
    if "db" not in g:
        g.db = mysql.connector.connect(user='forsen_minecraft_r', password=r_db_pw, host='127.0.0.1', database='forsen_minecraft')
    return g.db

def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

app.teardown_appcontext(close_db)

@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache"
    return response

@app.route("/time/latest", methods=["GET"])
def get_latest_time():
    if "streamer" not in request.args:
        return "streamer argument missing", 400
    streamer = request.args.get("streamer")
    db = get_db()
    cursor = db.cursor()
    cursor.execute(sql_get_latest_time, (streamer,))
    record = cursor.fetchone()
    cursor.close()
    db.commit()
    if (record is not None):
        (id_date, game_time, real_time) = record
        return { "date": id_date.isoformat(), "igt": game_time.total_seconds(), "rta": real_time.total_seconds() }
    else:
        return {}

@app.route("/time/history", methods=["GET"])
def get_time_history():
    if "streamer" not in request.args:
        return "streamer argument missing", 400
    streamer = request.args.get("streamer")
    if "from" not in request.args or "to" not in request.args:
        return "from or to missing", 400
    try:
        from_date = dt.datetime.fromisoformat(request.args.get("from"))
        to_date = dt.datetime.fromisoformat(request.args.get("to"))
    except ValueError:
        return "from or to is not a date", 400
    if to_date < from_date:
        return "to date comes before from date", 400
    if to_date - from_date > dt.timedelta(days=1):
        return "timespan between from and to is too large", 400
    db = get_db()
    cursor = db.cursor()
    cursor.execute(sql_get_time_history, (from_date, to_date, streamer))
    return_list = []
    for (id_date, game_time, real_time) in cursor:
        return_list.append({ "date": id_date.isoformat(), "igt": game_time.total_seconds(), "rta": real_time.total_seconds() })
    cursor.close()
    db.commit()
    return return_list