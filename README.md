# Forsen Minecraft Tracker
Website that tracks Forsen's Minecraft speedrunning timer.

https://piggeywig2000.com/forsenmc/

## How the site is hosted
The codebase is not the most elegant, but it was fast for me to write and kept things fairly simple.

- Uses a MySQL database to:
  - Store snapshots of the speedrun timer value at points in time (every 4 seconds).
  - Store push notification data to know where to send notifications to.
- The web API for fetching the speedrun times from the database and managing the notifications is a C# ASP.NET Core web app in [api/ForsenMinecraft](api/ForsenMinecraft).
  - It is run as HTTP to localhost using a Linux systemd service.
- Nginx is used to host the publicly facing web server.
  - It hosts the static files like the HTML, CSS, and JavaScript.
  - It acts as a reverse proxy for the web API server.
- [forsen_minecraft_time_scraper.py](forsen_minecraft_time_scraper.py) runs in the background continuously fetching frames from Forsen's stream and adding new speedrun times to the database.
  - It is run using a separate Linux systemd service.
- [forsen_minecraft_exporter.py](forsen_minecraft_exporter.py) creates a CSV dump of the database.
  - It is run once per day (at 05:00 UTC) by a cron job.

### MySQL Database
The database's schema is `forsen_minecraft`.

There is a table called `times`:
```sql
CREATE TABLE `times` (
  `id_date` datetime(3) NOT NULL,
  `id_streamer` varchar(32) NOT NULL,
  `game_time` time(3) NOT NULL,
  `real_time` time(3) NOT NULL,
  PRIMARY KEY (`id_date`, `id_streamer`)
);
```

There is a table called `notify_endpoints`:
```sql
CREATE TABLE `notify_endpoints` (
  `user_id` char(36) NOT NULL PRIMARY KEY,
  `endpoint` varchar(512) NOT NULL,
  `p256dh` varchar(256) NOT NULL,
  `auth` varchar(24) NOT NULL
);
```

There is a table called `notify_time_events`:
```sql
CREATE TABLE `notify_time_events` (
  `id` int UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT,
  `user_id` char(36) NOT NULL,
  `streamer` varchar(32) NOT NULL,
  `trigger_time` time(3) NOT NULL,
  FOREIGN KEY (`user_id`) REFERENCES `notify_endpoints`(`user_id`)
    ON DELETE CASCADE
);
CREATE INDEX `streamer` ON `notify_time_events` (`streamer`);
CREATE INDEX `trigger_time` ON `notify_time_events` (`trigger_time`);
```

There are two database users:
- `forsen_minecraft_r` with read-only permissions
- `forsen_minecraft_rw` with read/write permissions
  - `times` only needs SELECT and INSERT
  - `notify_endpoints` and `notify_time_events` needs SELECT, INSERT, UPDATE, and DELETE

### Secret files
In the root directory of the repository (the same directory as the Python scripts) there is a file called `secrets.json` containing database passwords and other settings used by the Python scripts. It contains the following values:

```json
{
    "database_r_pw": "PASSWORD FOR DATABASE USER forsen_minecraft_r",
    "database_rw_pw": "PASSWORD FOR DATABASE USER forsen_minecraft_rw",
    "csv_backup_path": "DIRECTORY TO WRITE THE CSV BACKUP TO (www/data to be served by Nginx)"
}
```

In `api/ForsenMinecraft` there is a file called `appsettings.Private.json` containing database connection strings and Vapid keys used by the web server. It contains the following values:
```json
{
  "ConnectionStrings": {
    "MainDbRead": "server=127.0.0.1;database=forsen_minecraft;user=forsen_minecraft_r;password=[INSERT PASSWORD HERE]",
    "MainDbReadWrite": "server=127.0.0.1;database=forsen_minecraft;user=forsen_minecraft_rw;password=[INSERT PASSWORD HERE]"
  },
  "Vapid": {
    "Subject": "mailto:[INSERT EMAIL ADDRESS HERE]",
    "PublicKey": "[INSERT VALID PUBLIC KEY HERE]",
    "PrivateKey": "[INSERT VAPID PRIVATE KEY HERE]"
  }
}
```
