"""Simple webRTC based usb-camera server for home use"""
import os
import json
import logging
import asyncio
from typing import NamedTuple
from functools import partial

import yaml
from aiohttp import web
from aiortc.rtcrtpsender import RTCRtpSender
from aiortc.contrib.media import MediaPlayer, MediaRelay
from aiortc import RTCPeerConnection, RTCSessionDescription

from CustomVideoTrack import CustomVideoTrack

ROOT = os.path.dirname(__file__)
PCS = set()



try:
    with open(os.path.join(ROOT,'settings.yaml'), 'r', encoding="utf-8") as file:
        config = yaml.safe_load(file)
except FileNotFoundError as exc:
    raise FileNotFoundError("[ ERR ] could not find settings.yaml file") from exc



CERT_FILE = config['CERT_FILE']
KEY_FILE = config['KEY_FILE']
HOST = config['HOST']
FRAME_RATE = config['FRAME_RATE']
RESOLUTION_WIDTH = config['RESOLUTION_WIDTH']
RESOLUTION_HEIGHT = config['RESOLUTION_HEIGHT']
PORT = config['PORT']
VERBOSE = config['VERBOSE']
JS_CONNECTION_TIME = config['MAX_CONNETION_TIME_SECS']
CAMERA_PATH = config['CAMERA_PATH']


class CameraSettings(NamedTuple):
    """Parameters for Camera"""
    framerate: str
    resolution: str


class CameraObject:
    """Create a camera object that is responsible for serving camera"""
    def __init__(self, settings: CameraSettings):
        self.settings = settings
        self.webcamera = None
        self.relay = None


    def initialize(self):
        """Camera initialization settings: OS check, webcamera port set"""
        options = {"framerate": self.settings.framerate, "video_size": self.settings.resolution}
        if self.relay is None:
            self.webcamera = MediaPlayer(CAMERA_PATH, format="v4l2", options=options)
            self.relay = MediaRelay()


    def get_video_track(self):
        """Get data from the camera"""
        if self.webcamera:
            return self.relay.subscribe(self.webcamera.video)
        return None



def create_local_tracks(camera_object):
    """Create local media tracks."""
    camera_object.initialize()
    video_track = CustomVideoTrack(camera_object.get_video_track())
    return None, video_track



def force_codec(pc, sender, forced_codec):
    """Force the codec to be used for the connection."""
    kind = forced_codec.split("/")[0]
    codecs = RTCRtpSender.getCapabilities(kind).codecs
    transceiver = next(t for t in pc.getTransceivers() if t.sender == sender)
    transceiver.setCodecPreferences(
        [codec for codec in codecs if codec.mimeType == forced_codec]
    )



async def index(_request):
    """Serve the index HTML."""
    with open(os.path.join(ROOT, "templates", "index.html"), "r", encoding="utf-8") as fl:
        return web.Response(content_type="text/html", text=fl.read())



async def javascript(_request):
    """Serve the client JavaScript."""
    with open(os.path.join(ROOT, "js", "client.js"), "r", encoding="utf-8") as fl:
        return web.Response(content_type="application/javascript", text=fl.read())


async def matrix(_request):
    """Serve the client JavaScript."""
    with open(os.path.join(ROOT, "js", "matrix.js"), "r", encoding="utf-8") as fl:
        return web.Response(content_type="application/javascript", text=fl.read())


async def server_config(_request):
    """Page for passing config data to Javascript"""
    # + Resolution if needed
    data = {'max_connection_time': JS_CONNECTION_TIME,
            'video_width': RESOLUTION_WIDTH,
            'video_height': RESOLUTION_HEIGHT
    }
    return web.json_response(data)



async def offer(request, camera_object):
    """Handle offer from client and create an answer."""
    params = await request.json()
    offer_ = RTCSessionDescription(sdp=params["sdp"], type=params["type"])
    print(offer_)

    pc = RTCPeerConnection()
    PCS.add(pc)

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        print(f"Connection state is {pc.connectionState}")
        if pc.connectionState == "failed":
            await pc.close()
            PCS.discard(pc)

    audio, video = create_local_tracks(camera_object)
    if audio:
        pc.addTrack(audio)

    if video:
        pc.addTrack(video)

    await pc.setRemoteDescription(offer_)

    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.Response(
        content_type="application/json",
        text=json.dumps(
            {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
        ),
    )



async def on_shutdown(_app):
    """Close all peer connections on shutdown."""
    coros = [pc.close() for pc in PCS]
    await asyncio.gather(*coros)
    PCS.clear()



if __name__ == "__main__":
    if VERBOSE:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    SSL_CONTEXT_DATA = None

    if len(CERT_FILE) > 0 and len(KEY_FILE) > 0:
        import ssl
        SSL_CONTEXT_DATA = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        try:
            SSL_CONTEXT_DATA.load_cert_chain(os.path.join(ROOT,CERT_FILE),
                os.path.join(ROOT,KEY_FILE))
        except FileNotFoundError as exc:
            raise FileNotFoundError("[ ERR ] No SSL files found, please provide a right path") from exc

    camera_settings = CameraSettings(framerate=str(FRAME_RATE),
        resolution=f"{RESOLUTION_WIDTH}x{RESOLUTION_HEIGHT}")
    camera_obj = CameraObject(settings=camera_settings)

    app = web.Application()
    app.on_shutdown.append(on_shutdown)
    app.router.add_get("/", index)
    app.router.add_static('/static', os.path.join(ROOT, "static"))
    app.router.add_get("/client.js", javascript)
    app.router.add_get("/matrix.js", matrix)
    app.router.add_get("/config", server_config)
    app.router.add_post("/offer", partial(offer, camera_object=camera_obj))

    web.run_app(app, host=HOST, port=PORT, ssl_context=SSL_CONTEXT_DATA)
