self.addEventListener("push", (e) => {
    if (!("showNotification" in self.registration) || self.Notification.permission != "granted") {
        return;
    }

    let data = e.data?.json() ?? {};
    let prettyName = data.streamer == "forsen" ? "Forsen" : (data.streamer == "xqc" ? "xQc" : data.streamer);

    self.registration.showNotification(`${prettyName} Minecraft Tracker`, {
        body: `${prettyName} has reached ${data.minutes} minutes`,
        icon: `notify-${data.streamer}-icon.png`,
        actions: [
            {
                action: `${data.streamer}-open-tracker`,
                title: "Open Tracker"
            },
            {
                action: `${data.streamer}-open-stream`,
                title: "Open Stream"
            }
        ],
        tag: `${data.streamer}-${data.minutes}`,
        renotify: true
    });
});

self.addEventListener("notificationclick", (e) => {
    if (!("action" in e)) {
        e.action = "";
    }

    let streamer = e.notification.tag.slice(0, e.notification.tag.indexOf("-"));

    let link = e.action != "" && e.action.includes("open-tracker") ? `/${streamer}mc` : `https://www.twitch.tv/${streamer}`;

    e.notification.close();

    if (clients.openWindow)
        e.waitUntil(clients.openWindow(link));
});
