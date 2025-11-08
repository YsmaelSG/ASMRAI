from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi import HTTPException
import os
import io
from pydantic import BaseModel
import asyncio
from dotenv import load_dotenv
from google import genai
# loads env variables into os enviroment to be SNATCHED
load_dotenv() 
api_curr_key = os.getenv("GEMINI_API_KEY")

class Video(BaseModel):
    response: str
    orderNumber: int


client = genai.Client(api_key=api_curr_key)
app = FastAPI()


@app.post("/")
async def getVideo(videoBody: Video):
    operation = client.models.generate_videos(
        model ="veo-3.1-generate-preview",
        prompt= str(videoBody.response),)
    
    while not operation.done:
        await asyncio.sleep(2)
        # Refresh the operation object to get the latest status.
        operation = client.operations.get(operation)

        if operation.error:
            raise HTTPException(
                status_code=500,
                detail="operation failed to load."
            )
    
    stream = io.BytesIO(operation.response.generatedVideos[0].video)

    return StreamingResponse(
        stream,
        media_type="video/mp4",
        headers={
            "Content-Disposition": 'inline; filename="generated.mp4"'
        }
    )  