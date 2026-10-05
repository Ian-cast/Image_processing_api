from base64 import encode
from fastapi import FastAPI, UploadFile
from fastapi.responses import StreamingResponse
from enum import Enum
import cv2
import numpy as np 
import io


app = FastAPI()

class Processing_type(str, Enum):
    grayscale = "Grayscale"
    negative="Negative"
    edges="Edges"

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.post("/upload_image")
async def upload_image(file: UploadFile):
    contents = await file.read()
    return{
        "filename": file.filename,
        "content_type": file.content_type,
        "size_in_bytes": len(contents)
    }
@app.post("/process_image")
async def process_image(file: UploadFile, processing_type: Processing_type= Processing_type.grayscale):
    contents = await file.read()
    np_array=np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
    if processing_type == Processing_type.grayscale:
        result= cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    elif processing_type == Processing_type.negative:
        result= cv2.bitwise_not(img)
    elif processing_type == Processing_type.edges:
        gray_img=cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        result= cv2.Canny(gray_img, 30, 70)
    success, encoded_image=cv2.imencode(".jpg", result)
    return StreamingResponse(io.BytesIO(encoded_image.tobytes()),media_type="image/jpeg")
    