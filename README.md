# Forsen Minecraft Tracker
Website that tracks Forsen's Minecraft speedrunning timer.

- Main site: https://piggeywig2000.com/forsenmc/
- Alternative GitHub pages mirror: https://piggeywig2000.github.io/forsen-minecraft/
  - Note that the GitHub pages mirror site still makes requests to the main site's API to fetch speedrun times. GitHub just hosts the static website files.

## How the site is hosted
The codebase is not the most elegant, but it was fast for me to write and kept things fairly simple.

- A MySQL database with a single table is used to store snapshots of the speedrun timer value at points in time (every 4 seconds).
- The web API for fetching the speedrun times from the database is a simple Python Flask script [forsen_minecraft_time.py](forsen_minecraft_time.py).
  - It is run by the Gunicorn web server to localhost only using a Linux systemd service.
- Nginx is used to host the publicly facing web server.
  - It hosts the static files like the HTML, CSS, and JavaScript.
  - It acts as a reverse proxy for the web API server.
- [forsen_minecraft_time_scraper.py](forsen_minecraft_time_scraper.py) runs in the background continuously fetching frames from Forsen's stream and adding new speedrun times to the database.
  - It is run using a separate Linux systemd service.
- [forsen_minecraft_exporter.py](forsen_minecraft_exporter.py) creates a CSV dump of the database.
  - It is run once per day (at 05:00 UTC) by a cron job.

### MySQL Database
The database contains a schema called `forsen_minecraft`, with a table called `times`:
```sql
CREATE TABLE `times` (
  `id_date` datetime(3) NOT NULL,
  `game_time` time(3) NOT NULL,
  `real_time` time(3) NOT NULL,
  PRIMARY KEY (`id_date`)
);
```

There are two database users:
- `forsen_minecraft_r` with read-only permissions to the times table
- `forsen_minecraft_rw` with read/write permissions to the times table

### Secrets.json
In the root folder of the repository (the same directory as the Python scripts) there is a file called `secrets.json` containing database passwords and other settings used by the Python scripts. It contains the following values:

```json
{
    "database_r_pw": "PASSWORD FOR DATABASE USER forsen_minecraft_r",
    "database_rw_pw": "PASSWORD FOR DATABASE USER forsen_minecraft_rw",
    "csv_backup_path": "PATH TO WRITE THE CSV BACKUP TO (www/data/forsen_minecraft.times.csv to be served by Nginx)"
}
```
