function timeout(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function fetchLatest() {
    let response = await fetch("https://piggeywig2000.com/forsenmc/api/time/latest", {cache: "no-store"});
    let entry = await response.json();
    return entry;
}

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