import csv
import json
import mysql.connector
from pathlib import Path
import sys

sql_get_count = "SELECT COUNT(id_date) FROM times WHERE id_streamer = %s"
sql_get_records = "SELECT id_date, game_time, real_time FROM times WHERE id_streamer = %s"

if len(sys.argv) < 2:
    raise Exception("No streamer argument supplied")
streamer_name = sys.argv[1]

with open(Path(__file__).parent.joinpath("secrets.json")) as secret_json_file:
    secrets = json.load(secret_json_file)
    r_db_pw = secrets["database_r_pw"]
    csv_backup_path = secrets["csv_backup_path"]

db = mysql.connector.connect(user='forsen_minecraft_r', password=r_db_pw, host='127.0.0.1', database='forsen_minecraft')

def get_count():
    cursor = db.cursor()
    cursor.execute(sql_get_count, (streamer_name,))
    return_val = cursor.fetchall()[0][0]
    cursor.close()
    return return_val

num_records = get_count()

with open(Path(csv_backup_path).joinpath(f"{streamer_name}_times.csv"), 'w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile)
    cursor = db.cursor()
    cursor.execute(sql_get_records, (streamer_name,))
    csvwriter.writerow(cursor.column_names)
    rows_written = 0
    last_percent = 0
    for (id_date, game_time, real_time) in cursor:
        csvwriter.writerow([id_date, game_time, real_time])
        rows_written += 1
        if int((rows_written / num_records) * 100) > last_percent:
            last_percent = int((rows_written / num_records) * 100)
            print(f"Written {rows_written}/{num_records} ({last_percent}%)")
    cursor.close()

db.close()

print("Done")