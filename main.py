
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from enum import Enum
import cv2
import numpy as np 
import io
from data_base import engine, SessionLocal
from db_models import ProcessedImage,Base
from PIL import Image, UnidentifiedImageError


Base.metadata.create_all(bind=engine)

app = FastAPI()
face_net = cv2.dnn.readNetFromCaffe("models/deploy.prototxt", "models/res10_300x300_ssd_iter_140000.caffemodel")

class Processing_type(str, Enum):
    grayscale = "Grayscale"
    negative="Negative"
    edges="Edges"
    face_detection="Face Detection"

MAX_FILENAME_LENGTH = 255
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_IMAGE_PIXELS = 16_000_000        # 16 megapixels, about 4000 x 4000
def log_processed_image(filename: str | None, processing_type: str) -> None:
    db = SessionLocal()
    try:
        db.add(ProcessedImage(
            filename=(filename or "unknown")[:MAX_FILENAME_LENGTH],
            processing_type=processing_type,
        ))
        db.commit()
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.post("/process_image")
async def process_image(file: UploadFile, processing_type: Processing_type= Processing_type.grayscale):
    
    contents = await file.read(MAX_UPLOAD_BYTES + 1)
    if not contents:
        raise HTTPException(status_code=400, detail="Empty file. Please upload an image.")
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. The maximum size is {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.",
        )

    # Read only the image header to get its dimensions, without decoding the pixels.
    try:
        with Image.open(io.BytesIO(contents)) as probe:
            width, height = probe.size
    except Image.DecompressionBombError:
        raise HTTPException(status_code=422, detail="Image dimensions are too large.")
    except (UnidentifiedImageError, OSError):
        raise HTTPException(
            status_code=415,
            detail="Could not read the file as an image. Please upload a valid image file (JPG, PNG, BMP, etc.).",
        )

    if width * height > MAX_IMAGE_PIXELS:
        raise HTTPException(
            status_code=422,
            detail=f"Image too large. The maximum is {MAX_IMAGE_PIXELS // 1_000_000} megapixels.",
        )

    np_array = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

    if img is None:
        raise HTTPException(
            status_code=415,
            detail="Could not decode image. Please upload a valid image file (JPG, PNG, BMP, etc.).",
        )
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

    log_processed_image(file.filename, processing_type.value)
    
    return StreamingResponse(io.BytesIO(encoded_image.tobytes()),media_type="image/jpeg")
    