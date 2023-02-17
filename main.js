var currentTimeElement;
var historyUpToElement;
var mainChart;
var historyPage;
var alertCheckboxElement;

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
    let timeOffset = moment() - lastUpdateTime;
    let currentTime = lastUpdateValue + timeOffset;
    if (timeOffset < moment.duration(2, "minutes")) {
        currentTimeElement.textContent = `IGT: ${getTimespanString(currentTime, true)}`;
        currentTimeElement.style.visibility = "";

        if (alertEnabled && currentTime > alertTime) {
            alertAudio.play();
        }
        else {
            alertAudio.pause();
            alertAudio.currentTime = 0;
        }
    }
    else {
        currentTimeElement.style.visibility = "hidden";

        alertAudio.pause();
        alertAudio.currentTime = 0;
    }
}

async function loadLatest() {
    let response = await fetch("https://piggeywig2000.com/forsenmc/api/time/latest");
    let entry = await response.json();
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
    from = from.substring(0, from.length - 1)
    let response = await fetch(`https://piggeywig2000.com/forsenmc/api/time/history?from=${from}&to=${to}`);
    let entries = await response.json();
    entries.forEach(entry => {
        di = convertEntryToDataItem(entry);
        data.unshift(di);
    });
    mainChart?.update();
}

async function init() {
    try {
        let entry = await loadLatest();
        historyPage = convertGenericDateStringToTimezone(entry.date);
        setInterval(loadLatest, 4000);
        setInterval(updateLiveTimer, 7);
        await loadHistory();
    }
    catch (err) {
        alert("Failed to connect. The server is probably down.");
    }
}

window.addEventListener("load", async () => {
    Chart.defaults.color = "#aaa";
    currentTimeElement = document.getElementById("currentTime");
    historyUpToElement = document.getElementById("historyUpTo");
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
        alertContainerElement.style.maxHeight = alertCheckboxElement.checked ? "8rem" : "0";
        refreshAlert();
    });
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
        refreshAlert();
    });
    let alertVolume = document.getElementById("volumeInput");
    alertVolume.addEventListener("input", () => alertAudio.volume = alertVolume.value * alertVolume.value);
});