import csv
import json
import mysql.connector
import os

sql_get_count = "SELECT COUNT(id_date) FROM times"
sql_get_records = "SELECT id_date, game_time, real_time FROM times"

with open(os.path.join(os.path.dirname(__file__), "secrets.json")) as secret_json_file:
    secrets = json.load(secret_json_file)
    r_db_pw = secrets["database_r_pw"]
    csv_backup_path = secrets["csv_backup_path"]


db = mysql.connector.connect(user='forsen_minecraft_r', password=r_db_pw, host='127.0.0.1', database='forsen_minecraft')

def get_count():
    cursor = db.cursor()
    cursor.execute(sql_get_count)
    return_val = cursor.fetchall()[0][0]
    cursor.close()
    return return_val

num_records = get_count()

with open(csv_backup_path, 'w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile)
    cursor = db.cursor()
    cursor.execute(sql_get_records)
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