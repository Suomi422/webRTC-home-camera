import asyncio
import cv2
import numpy as np
import torch

from aiortc import VideoStreamTrack
from av import VideoFrame

class CustomVideoTrack(VideoStreamTrack):
    """
    A video stream track that draws a red rectangle on every frame.
    """
    def __init__(self, track):
        super().__init__()
        self.model = torch.hub.load("ultralytics/yolov5", "yolov5s")
        self.track = track

    async def recv(self):
        # 1. Receive a frame from the original track.
        frame = await self.track.recv()

        # 2. Convert the frame to a NumPy array in BGR format (for OpenCV).
        img = frame.to_ndarray(format="bgr24")

        # perform inference
        results = self.model(img)
        
        detections = results.xyxy[0].cpu().numpy() # Move to CPU and convert to NumPy array
        for *xyxy, conf, cls in detections:
            xmin, ymin, xmax, ymax = map(int, xyxy) # Convert coordinates to integers
            label = self.model.names[int(cls)] # Get class name from class ID
            confidence = f"{conf:.2f}"

            # Draw rectangle
            color = (0, 255, 0) # Green color for bounding box
            thickness = 2
            cv2.rectangle(img, (xmin, ymin), (xmax, ymax), color, thickness)

            # Put label and confidence
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.7
            font_thickness = 2
            text = f"{label}: {confidence}"
            cv2.putText(img, text, (xmin, ymin - 10), font, font_scale, color, font_thickness, cv2.LINE_AA)

        # 4. Rebuild the video frame from the modified NumPy array.
        new_frame = VideoFrame.from_ndarray(img, format="bgr24")
        
        # Preserve the original timing information to avoid stuttering.
        new_frame.pts = frame.pts
        new_frame.time_base = frame.time_base
        
        # 5. Return the modified frame.
        return new_frame