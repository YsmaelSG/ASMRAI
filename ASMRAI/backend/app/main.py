from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import FileResponse
from google import genai
from google.genai import types

import time


class Video(BaseModel):
    response: str
    orderNumber: int


cilent = genai.Cilent()
app = FastAPI()


@app.post("/")
async def getVideo(videoBody: Video):
    operation = cilent.models.generate_videos(
        model ="veo-3.1-generate-preview",
        prompt= str(videoBody.response),)
    
    while not operation.done:
        time.sleep(10)
        # Refresh the operation object to get the latest status.
        operation = client.operations.get(operation)
    
    return FileResponse(operation.response.generatedVideos[0].video, media_type="video/mp4")
    