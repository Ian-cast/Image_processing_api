from base64 import encode
from fastapi import FastAPI, UploadFile
from fastapi.responses import StreamingResponse
import cv2
import numpy as np 
import io


app = FastAPI()

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
async def process_image(file: UploadFile):
    contents = await file.read()
    np_array=np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
    gray_img= cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    success, encoded_image=cv2.imencode(".jpg", gray_img)
    return StreamingResponse(io.BytesIO(encoded_image.tobytes()),media_type="image/jpeg")