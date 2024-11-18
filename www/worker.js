var streamer = null;

onmessage = (e) => {
    if (streamer == null) {
        streamer = e.data.streamer;
        
        (async() => {
            while (true) {
                let reloadTimer = timeout(4000);
                try {
                    let entry = await fetchLatest();
                    postMessage({type: "success", value: entry});
                }
                catch (ex) {
                    postMessage({type: "fail", value: ex});
                }
                finally {
                    await reloadTimer;
                }
            }
        })()
    }
};

function timeout(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function fetchLatest() {
    let response = await fetch(`https://piggeywig2000.dev/forsenmc/api/time/latest?streamer=${streamer}`, {cache: "no-store"});
    let entry = await response.json();
    return entry;
}
