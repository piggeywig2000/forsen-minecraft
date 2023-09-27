const NOTIFICATION_TIME_TEMPLATE = "";

var notificationRequestSectionElement = null;
var notificationRequestButtonElement = null;
var notificationBlockedErrorElement = null;

var notificationSectionElement = null;
var notificationContainerElement = null;
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
    try {
        let swRegistration = await navigator.serviceWorker.register("service-worker.js?v=" + VERSION_HASH);
        await navigator.serviceWorker.ready;
        let pushSubscription = await swRegistration.pushManager.getSubscription();
        if (pushSubscription == null) {
            pushSubscription = await swRegistration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: "BGRl1E3oYM6QjxBuv79h7XL2FKi3IRPgTrYacbp9y6ycPm1FILfCcQNWaZkPBNM4oyEYAFDQylI7BKbRJwlGCvE"
            });
        }
        subscriptionInfo = pushSubscription.toJSON();
        subscriptionInfo.userId = userId;
        let response = await fetch("https://piggeywig2000.com/forsenmc/api/notification/register", {
            method: "POST",
            cache: "no-store",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(subscriptionInfo)
        });
        if (!response.ok) {
            throw response.status;
        }
        await sendTimeEvents();
    }
    catch {
        notificationRequestSectionElement.style.display = "none";
        notificationSectionElement.style.display = "none";
    }
    finally {
        hideLoading();
    }
}

async function sendTimeEvents() {
    showLoading();
    try {
        let triggerMinutes = notificationCheckboxElement.checked ? getTimeEventsInContainer() : [];
        let response = await fetch("https://piggeywig2000.com/forsenmc/api/notification/time_events", {
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
        if (!response.ok) {
            throw response.status;
        }
    }
    catch {
        notificationRequestSectionElement.style.display = "none";
        notificationSectionElement.style.display = "none";
    }
    finally {
        hideLoading();
    }
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
        refreshSwipeVerticalHeight(notificationContainerElement);
        onTimeEventsChange();
        await sendTimeEvents();
    });
    notificationTimesContainerElement.appendChild(newElement);
    refreshSwipeVerticalHeight(notificationContainerElement);
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
    notificationContainerElement = document.getElementById("notificationContainer");
    notificationCheckboxElement = document.getElementById("enableNotifications");
    notificationTimesContainerElement = document.getElementById("notificationTimesContainer");
    notificationTimesItemTemplate = document.getElementById("notificationTimesItemTemplate");
    notificationNewTimeSelectElement = document.getElementById("notificationNewTimeSelect");
    notificationNewTimeButtonElement = document.getElementById("notificationNewTimeButton");

    let notificationQuietWarningElement = document.getElementById("notificationQuietWarning");
    notificationRequestButtonElement.addEventListener("click", async () => {
        notificationRequestButtonElement.disabled = true;
        notificationQuietWarningElement.style.display = "";
        await Notification.requestPermission();
        notificationRequestButtonElement.disabled = false;
        notificationQuietWarningElement.style.display = "none";
        await updatePermissionChanged();
    });

    notificationCheckboxElement.addEventListener("change", async (e) => {
        if (notificationCheckboxElement.checked) {
            notificationContainerElement.classList.remove("swipe-vertical-animation-hidden");
            refreshSwipeVerticalHeight(notificationContainerElement);
        }
        else {
            notificationContainerElement.classList.add("swipe-vertical-animation-hidden");
        }
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
    swipeVerticalAnimationResizeObserver.observe(notificationContainerElement);

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