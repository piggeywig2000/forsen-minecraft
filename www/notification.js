const NOTIFICATION_TIME_TEMPLATE = "";

var notificationRequestSectionElement = null;
var notificationRequestButtonElement = null;
var notificationBlockedErrorElement = null;

var notificationSectionElement = null;
var notificationCheckboxElement = null;
var notificationTimesContainerElement = null;
var notificationTimesItemTemplate = null;
var notificationNewTimeSelectElement = null;
var notificationNewTimeButtonElement = null;

var userId = null;

async function updatePermissionChanged() {
    let requestResult = Notification.permission;
    notificationRequestSectionElement.style.display = (requestResult == "granted") ? "none" : "";
    notificationRequestButtonElement.disabled = requestResult == "denied";
    notificationBlockedErrorElement.style.display = (requestResult == "denied") ? "" : "none";
    notificationSectionElement.style.display = (requestResult == "granted") ? "" : "none";

    if (requestResult == "granted" && notificationCheckboxElement.checked) {
        await setupPush();
    }
}

async function setupPush() {
    showLoading();
    console.log("setup push");
    let swRegistration = await navigator.serviceWorker.register("service-worker.js?v=" + VERSION_HASH);
    let pushSubscription = await swRegistration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: "BGRl1E3oYM6QjxBuv79h7XL2FKi3IRPgTrYacbp9y6ycPm1FILfCcQNWaZkPBNM4oyEYAFDQylI7BKbRJwlGCvE"
    });
    subscriptionInfo = pushSubscription.toJSON();
    subscriptionInfo.userId = userId;
    await fetch("https://piggeywig2000.com/forsenmc/api/notification/register", {
        method: "POST",
        cache: "no-store",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(subscriptionInfo)
    });
    await sendTimeEvents();
    hideLoading();
}

async function sendTimeEvents() {
    showLoading();
    let triggerMinutes = notificationCheckboxElement.checked ? getTimeEventsInContainer() : [];
    console.log(`sending ${notificationCheckboxElement.checked} and ${triggerMinutes}`);
    await fetch("https://piggeywig2000.com/forsenmc/api/notification/time_events", {
        method: "POST",
        cache: "no-store",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            userId: userId,
            streamer: STREAMER,
            triggerMinutes: triggerMinutes
        })
    });
    hideLoading();
}

function getTimeEventsInContainer() {
    let output = [];
    for (let item of notificationTimesContainerElement.children) {
        output.push(parseInt(item.getAttribute("minutes")));
    }
    return output;
}

function addTimeEventToContainer(numMinutes) {
    let newElement = notificationTimesItemTemplate.content.cloneNode(true);
    newElement.querySelector(".multi-element-item").setAttribute("minutes", numMinutes.toString());
    newElement.querySelector(".multi-element-item").style.order = numMinutes.toString();
    newElement.querySelector(".multi-element-item-text").textContent = `${numMinutes} minutes`;
    newElement.querySelector(".multi-element-delete-button").addEventListener("click", async (e) => {
        e.target.closest(".multi-element-item").remove();
        onTimeEventsChange();
        await sendTimeEvents();
    });
    notificationTimesContainerElement.appendChild(newElement);
}

function onTimeEventsChange() {
    let selectedMinutes = parseInt(notificationNewTimeSelectElement.value);
    notificationNewTimeButtonElement.disabled = getTimeEventsInContainer().includes(selectedMinutes);
    window.localStorage.setItem(`${STREAMER}-notification-minutes`, JSON.stringify(getTimeEventsInContainer()));
}

async function initNotification() {
    //Check for JS support
    if (!("Notification" in window) || !('serviceWorker' in navigator) || !('PushManager' in window)) {
        return;
    }

    notificationRequestSectionElement = document.getElementById("notificationRequestSection");
    notificationRequestButtonElement = document.getElementById("requestNotificationsButton");
    notificationBlockedErrorElement = document.getElementById("notificationBlockedError");

    notificationSectionElement = document.getElementById("notificationSection");
    notificationCheckboxElement = document.getElementById("enableNotifications");
    notificationTimesContainerElement = document.getElementById("notificationTimesContainer");
    notificationTimesItemTemplate = document.getElementById("notificationTimesItemTemplate");
    notificationNewTimeSelectElement = document.getElementById("notificationNewTimeSelect");
    notificationNewTimeButtonElement = document.getElementById("notificationNewTimeButton");

    notificationRequestButtonElement.addEventListener("click", async () => {
        notificationRequestButtonElement.disabled = true;
        await Notification.requestPermission();
        notificationRequestButtonElement.disabled = false;
        await updatePermissionChanged();
    });

    let notificationContainerElement = document.getElementById("notificationContainer");
    notificationCheckboxElement.addEventListener("change", async (e) => {
        notificationContainerElement.style.maxHeight = notificationCheckboxElement.checked ? "10rem" : "0";
        if (e.isTrusted) {
            if (notificationCheckboxElement.checked) {
                await setupPush();
            }
            else {
                await sendTimeEvents();
            }
        }
        window.localStorage.setItem(`${STREAMER}-notification-enabled`, notificationCheckboxElement.checked);
    });

    notificationNewTimeSelectElement.addEventListener("change", () => {
        onTimeEventsChange();
    });

    notificationNewTimeButtonElement.addEventListener("click", async () => {
        let selectedMinutes = parseInt(notificationNewTimeSelectElement.value);
        if (getTimeEventsInContainer().includes(selectedMinutes)) {
            return;
        }
        addTimeEventToContainer(selectedMinutes);
        onTimeEventsChange();
        await sendTimeEvents();
    });

    //Generate user ID if we don't already have one
    userId = window.localStorage.getItem(`user-id`);
    if (userId == null) {
        userId = crypto.randomUUID();
        window.localStorage.setItem(`user-id`, userId);
    }

    notificationCheckboxElement.checked = window.localStorage.getItem(`${STREAMER}-notification-enabled`) == "true";
    notificationCheckboxElement.dispatchEvent(new Event("change"));

    for (let timeEvent of JSON.parse(window.localStorage.getItem(`${STREAMER}-notification-minutes`) ?? "[]")) {
        addTimeEventToContainer(timeEvent);
    }
    onTimeEventsChange();

    await updatePermissionChanged();
}