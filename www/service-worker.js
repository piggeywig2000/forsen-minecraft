self.addEventListener("push", (e) => {
    if (!("showNotification" in self.registration) || self.Notification.permission != "granted") {
        return;
    }

    self.registration.showNotification("Forsen Minecraft Tracker", {
        body: "This is a test notification",
        actions: [
            {
                action: "open-tracker",
                title: "Open Tracker"
            },
            {
                action: "open-stream",
                title: "Open Stream"
            }
        ]
    });
});