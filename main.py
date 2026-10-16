from dbm import dumb
from base64 import encode
from fastapi import FastAPI, UploadFile
from fastapi.responses import StreamingResponse
from enum import Enum
import cv2
import numpy as np 
import io
from data_base import engine, SessionLocal
from db_models import ProcessedImage,Base

Base.metadata.create_all(bind=engine)

app = FastAPI()
face_net = cv2.dnn.readNetFromCaffe("models/deploy.prototxt", "models/res10_300x300_ssd_iter_140000.caffemodel")

class Processing_type(str, Enum):
    grayscale = "Grayscale"
    negative="Negative"
    edges="Edges"
    face_detection="Face Detection"

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

    if img is None:
        return {"error": "Could not decode image. Please upload a valid image file (JPG, PNG, BMP, etc.)."}

    if processing_type == Processing_type.grayscale:
        result= cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    elif processing_type == Processing_type.negative:
        result= cv2.bitwise_not(img)
    elif processing_type == Processing_type.edges:
        gray_img=cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        result= cv2.Canny(gray_img, 30, 70)
    elif processing_type == Processing_type.face_detection:
        result = img.copy()
        (h, w) = img.shape[:2]
        blob = cv2.dnn.blobFromImage(cv2.resize(img, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0))
        face_net.setInput(blob)
        detections = face_net.forward()

        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            if confidence > 0.5:
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (startX, startY, endX, endY) = box.astype("int")
                cv2.rectangle(result, (startX, startY), (endX, endY), (0, 255, 0), 2)
    
    success, encoded_image=cv2.imencode(".jpg", result)

    db = SessionLocal()
    new_record = ProcessedImage(filename=file.filename, processing_type=processing_type.value)
    db.add(new_record)
    db.commit()
    db.close()
    
    return StreamingResponse(io.BytesIO(encoded_image.tobytes()),media_type="image/jpeg")
    