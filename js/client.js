// Define PlayerStatus as a constant
const PlayerStatus = {
RUNNING: 'running',
STOP: 'stop',
};


// Initialize variables
let pc = null;
let startTime = null;
let maxTimeInterval = 60;
const checkInterval = 1000;
const timeElement = document.getElementById('time');
let currentStatus = PlayerStatus.STOP;


// Async IIFE to fetch configuration
(async () => {
    try {
        const response = await fetch('/config');
        const data = await response.json();
        maxTimeInterval = data.max_connection_time;
    } catch (error) {
        console.error('[ ERR ] Error fetching config data (settings.yaml). Using default: ', error);
    } finally {
        updateTimeText(maxTimeInterval);
    }
})();


// Function to update the displayed time text
function updateTimeText(timeLeft) {
    timeElement.innerText = `Streaming time left: ${Math.floor(timeLeft)} seconds`;
}


// Function to negotiate connection
async function negotiate() {
    try {
        pc.addTransceiver('video', { direction: 'recvonly' });
        pc.addTransceiver('audio', { direction: 'recvonly' });

        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);

        await new Promise((resolve) => {
            if (pc.iceGatheringState === 'complete') {
                resolve();
            } else {
                const checkState = () => {
                    if (pc.iceGatheringState === 'complete') {
                        pc.removeEventListener('icegatheringstatechange', checkState);
                        resolve();
                    }
                };
                pc.addEventListener('icegatheringstatechange', checkState);
            }
        });

        const response = await fetch('/offer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                sdp: pc.localDescription.sdp,
                type: pc.localDescription.type,
            }),
        });

        const answer = await response.json();
        await pc.setRemoteDescription(answer);
    } catch (e) {
        alert(e);
    }
}


// Function to start streaming
function start() {
    currentStatus = PlayerStatus.RUNNING;
    pc = new RTCPeerConnection({ sdpSemantics: 'unified-plan' });
    startTime = Date.now();
    setInterval(checkConnectionDuration, checkInterval);

    pc.addEventListener('track', (evt) => {
        const elementId = evt.track.kind === 'video' ? 'video' : 'audio';
        document.getElementById(elementId).srcObject = evt.streams[0];
    });

    toggleView();
    toggleButtons();
    negotiate();
}


// Function to stop streaming
function stop() {
    currentStatus = PlayerStatus.STOP;
    toggleView();
    toggleButtons();

    if (pc) {
        setTimeout(() => {
        pc.close();
        pc = null;
        timeElement.classList.remove('Pulse');
        updateTimeText(maxTimeInterval);
        }, 500);
    }
}


// Function to check connection duration
function checkConnectionDuration() {
    if (pc && startTime) {
        const elapsedTime = (Date.now() - startTime) / 1000;
        const timeLeft = Math.max(0, maxTimeInterval - elapsedTime);
        updateTimeText(timeLeft);
        timeElement.classList.add('Pulse');

        if (elapsedTime > maxTimeInterval) {
            stop();
        }
    }
}


// Function to toggle start/stop buttons visibility
function toggleButtons() {
    document.getElementById('start').style.display = currentStatus === PlayerStatus.RUNNING ? 'none' : 'inline-block';
    document.getElementById('stop').style.display = currentStatus === PlayerStatus.RUNNING ? 'inline-block' : 'none';
}


// Function to toggle media view visibility
function toggleView() {
    document.getElementById('media').style.display = currentStatus === PlayerStatus.RUNNING ? 'block' : 'none';
}
