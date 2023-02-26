const VERSION_HASH = "e6825ad2a4b6f72ab4aeabddbf9db472c8d3428d";

var currentTimeElement = null;
var currentTime = null;
var snoozeButtonElement = null;
var snoozeTime = null;
var historyUpToElement = null;
var mainChart = null;
var historyPage = null;
var alertCheckboxElement = null;

var lastUpdateTime;
var lastUpdateValue;

var alertMinutes = null;
var alertSeconds = null;
var alertEnabled = false;
var alertTime;

var alertAudio = new Audio("dangeralarm.mp3");
alertAudio.loop = true;
alertAudio.volume = 0.25;

var data = [];

function refreshAlert() {
    alertEnabled = alertMinutes != null && alertSeconds != null && alertCheckboxElement.checked;
    if (alertEnabled) {
        alertTime = moment.duration({minutes: alertMinutes, seconds: alertSeconds});
    }
}

function playAlert() {
    alertAudio.play();
    snoozeButtonElement.style.maxHeight = "3rem";
    snoozeTime = null;
}

function stopAlert() {
    alertAudio.pause();
    alertAudio.currentTime = 0;
    snoozeButtonElement.style.maxHeight = "0";
    if (snoozeTime != null && (currentTime < snoozeTime || !alertEnabled || alertTime > currentTime)) {
        snoozeTime = null;
    }
}

function getTimespanString(value, includeMilliseconds) {
    let duration = moment.duration(value);
    let minutes = Math.floor(duration.asMinutes()).toString().padStart(2, '0');
    let seconds = duration.seconds().toString().padStart(2, '0');
    let milliseconds = Math.floor(duration.milliseconds()).toString().padStart(3, '0');
    return includeMilliseconds ? `${minutes}:${seconds}.${milliseconds}` : `${minutes}:${seconds}`
}

function convertGenericDateStringToTimezone(date) {
    return moment(date + "Z").local();
}

function convertEntryToDataItem(entry) {
    return { x: convertGenericDateStringToTimezone(entry.date).toISOString(true), y: entry.igt * 1000 };
}

function updateLiveTimer() {
    if (currentTimeElement == null) return;
    let timeOffset = moment() - lastUpdateTime;
    currentTime = lastUpdateValue + timeOffset;
    if (timeOffset < moment.duration(2, "minutes")) {
        currentTimeElement.textContent = `IGT: ${getTimespanString(currentTime, true)}`;
        currentTimeElement.style.visibility = "";

        if (alertEnabled && (currentTime > alertTime) && (snoozeTime == null || currentTime < snoozeTime)) {
            playAlert();
        }
        else {
            stopAlert();
        }
    }
    else {
        currentTimeElement.style.visibility = "hidden";
        stopAlert();
    }
}

function appendLatest(entry) {
    let dataItem = convertEntryToDataItem(entry);
    if (!data.some((e) => e.x == dataItem.x)) {
        data.push(dataItem);
        mainChart?.update();
        lastUpdateValue = moment.duration(dataItem.y);
        lastUpdateTime = convertGenericDateStringToTimezone(entry.date);
    }
    return entry;
}

async function loadHistory() {
    let to = historyPage.toISOString();
    to = to.substring(0, to.length - 1)
    historyPage.subtract(1, "hours");
    historyUpToElement.textContent = `Loaded up to: ${historyPage.format("LL HH:mm:ss")}`;
    let from = historyPage.toISOString();
    from = from.substring(0, from.length - 1);
    
    let response = await fetch(`https://piggeywig2000.com/forsenmc/api/time/history?from=${from}&to=${to}`, {cache: "no-store"});
    let entries = await response.json();
    if (entries.length == 0) return;

    let latestEntry = convertEntryToDataItem(entries[0]);
    let insertIndex = data.findIndex((element) => latestEntry.x <= element.x);
    insertIndex = insertIndex < 0 ? data.length : insertIndex;
    entries.forEach(entry => {
        di = convertEntryToDataItem(entry);
        data.splice(insertIndex, 0, di);
    });
    mainChart?.update();
}

async function init() {
    let hasInit = false;
    let liveUpdateWorker = new Worker("worker.js?v=" + VERSION_HASH);
    liveUpdateWorker.onmessage = (e) => {
        if (e.data.type == "fail") {
            if (!hasInit) {
                alert("Failed to connect. The server is probably down.");
                hasInit = true;
            }
            throw e.data.value;
        }

        let entry = e.data.value;
        appendLatest(entry);
        if (!hasInit) {
            historyPage = convertGenericDateStringToTimezone(entry.date);
            let liveTimerInterval = setInterval(updateLiveTimer, 7);
            document.addEventListener("visibilitychange", () => {
                if (document.visibilityState == "visible" && liveTimerInterval == null) {
                    liveTimerInterval = setInterval(updateLiveTimer, 7);
                }
                else if (document.visibilityState == "hidden" && liveTimerInterval != null) {
                    clearInterval(liveTimerInterval);
                    liveTimerInterval = null;
                }
            });
            loadHistory();
            hasInit = true;
        }
        updateLiveTimer();
    };
}

window.addEventListener("load", async () => {
    Chart.defaults.color = "#aaa";
    currentTimeElement = document.getElementById("currentTime");
    historyUpToElement = document.getElementById("historyUpTo");
    snoozeButtonElement = document.getElementById("snoozeButton");
    mainChart = new Chart(document.getElementById("chart"), {
        type: "line",
        data: {
            datasets: [{
                data: data,
                label: "In Game Time",
                borderColor: "rgb(54, 162, 235)",
                backgroundColor: "rgba(54, 162, 235, 0.5)"
            }]
        },
        options: {
            scales: {
                x: {
                    type: 'time',
                    title: {
                        text: "Real life time",
                        display: true
                    },
                    time: {
                        minUnit: "second",
                        tooltipFormat: "LL HH:mm:ss",
                        displayFormats: {
                            "millisecond": "HH:mm:ss.SSS",
                            "second": "HH:mm:ss",
                            "minute": "HH:mm",
                            "hour": "HH"
                        }
                    }
                },
                y: {
                    type: 'time',
                    title: {
                        text: "Speedrun time",
                        display: true
                    },
                    min: 0,
                    time: {
                        unit: "second",
                        displayFormats: {
                            "second": "mm:ss"
                        },
                        tooltipFormat: "mm:ss.SSS"
                    },
                    ticks: {
                        callback: function(value, index, ticks) {
                            return getTimespanString(value, false);
                        }
                    }
                }
            },
            elements: {
                point: {
                    pointRadius: 0,
                    pointHitRadius: 32,
                    pointHoverRadius: 6
                }
            },
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                zoom: {
                    pan: {
                        enabled: true,
                        mode: 'x'
                    },
                    zoom: {
                        wheel: {
                            enabled: true,
                            speed: 0.15
                        },
                        pinch: {
                            enabled: true
                        },
                        mode: 'x'
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                label += getTimespanString(context.parsed.y, true);
                            }
                            return label;
                        }
                    }
                },
                legend: {
                    display: false
                }
            }
        }
    });
    data = mainChart.data.datasets[0].data;
    init();
    document.getElementById("resetZoomButton").addEventListener("click", mainChart.resetZoom)
    document.getElementById("historyButton").addEventListener("click", loadHistory);
    let alertContainerElement = document.getElementById("alertContainer");
    alertCheckboxElement = document.getElementById("enableAlert");
    alertCheckboxElement.addEventListener("click", () => {
        alertContainerElement.style.maxHeight = alertCheckboxElement.checked ? "17rem" : "0";
        window.localStorage.setItem("alerts-enabled", alertCheckboxElement.checked);
        refreshAlert();
    });

    let hasClickedAnywhere = false;
    document.addEventListener("mousedown", () => {
        if (hasClickedAnywhere) return;
        document.getElementById("noSoundWarning").style.display = "none";
        hasClickedAnywhere = true;
    }, true);

    //Alerts
    let alertMinutesElement = document.getElementById("alertMinutes");
    let alertSecondsElement = document.getElementById("alertSeconds");
    alertMinutesElement.addEventListener("change", () => {
        let val = parseInt(alertMinutesElement.value);
        if (isNaN(val)) {
            alertMinutesElement.value = "";
            val = null;
        }
        else {
            val = Math.max(val, 0);
            alertMinutesElement.value = val.toString();
        }
        alertMinutes = val;
        window.localStorage.setItem("alerts-minutes", alertMinutes);
        refreshAlert();
    });
    alertSecondsElement.addEventListener("change", () => {
        let val = parseInt(alertSecondsElement.value);
        if (isNaN(val)) {
            alertSecondsElement.value = "";
            val = null;
        }
        else {
            val = Math.min(Math.max(val, 0), 59);
            alertSecondsElement.value = val.toString().padStart(2, '0');
        }
        alertSeconds = val;
        window.localStorage.setItem("alerts-seconds", alertSeconds);
        refreshAlert();
    });
    let alertVolumeElement = document.getElementById("volumeInput");
    alertVolumeElement.addEventListener("input", () => {
        alertAudio.volume = alertVolumeElement.value * alertVolumeElement.value
        window.localStorage.setItem("alerts-volume", alertVolumeElement.value);
    });
    
    snoozeButtonElement.addEventListener("click", () => {
        snoozeTime = alertTime;
    });

    //Local storage stuff
    if (window.localStorage.getItem("alerts-enabled") == "true") {
        alertCheckboxElement.checked = true;
        alertCheckboxElement.dispatchEvent(new Event("click"));
    }
    alertMinutesElement.value = window.localStorage.getItem("alerts-minutes");
    alertMinutesElement.dispatchEvent(new Event("change"));
    alertSecondsElement.value = window.localStorage.getItem("alerts-seconds");
    alertSecondsElement.dispatchEvent(new Event("change"));
    alertVolumeElement.value = window.localStorage.getItem("alerts-volume");
    alertVolumeElement.dispatchEvent(new Event("input"));
});