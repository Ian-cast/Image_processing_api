from fastapi import FastAPI, UploadFile

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.post("/upload-image")
async def upload_image(file: UploadFile):
    contents = await file.read()
    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "size_in_bytes": len(contents)
    }