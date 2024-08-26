# webRTC-home-camera
I was searching for a simple USB camera streaming solution for my home server that is not resource-intensive and does not use too much data. Unable to find anything that met my needs, I decided to write one myself.

This repository contains a simple web server intended to be run only on a local area network (LAN) in development mode. It does not include advanced production features.
The server can serve multiple requests at once and also has a timer that will disconnect clients, if they are connected for too long.
(I hate it when I use cellular data and forgot to close the connection)

Before running the server, please install the required packages listed in req.txt by executing:
`pip install -r req.txt`.

Next, review the settings.yaml file and adjust the settings to suit your needs. The default settings should work for most mid-range webcams. Here are the settings I use:

```
CERT_FILE: "cert.pem"
KEY_FILE: "key.pem"
HOST: "0.0.0.0"
PORT: 8080
FRAME_RATE: 30
RESOLUTION_WIDTH: 1280
RESOLUTION_HEIGHT: 720
CAMERA_PATH: "/dev/video0"
VERBOSE: false
MAX_CONNETION_TIME_SECS: 30
```
After configuring the settings, you can run the code using:
```python3 app.py```

You can then access the server from your PC's IP address and port (e.g., http://<your-ip>:8080). If you are using certificates like I am, you can also use `https://`.
The final result should look something like this. (By the way, I included a fancy matrix animation that I like, lol.)


![Screenshot_20240826_151752](https://github.com/user-attachments/assets/3f584589-ab4a-472c-a828-a88b3001b43c)
