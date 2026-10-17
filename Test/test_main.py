from fastapi.testclient import TestClient
from PIL import Image
import io
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from main import app

client = TestClient(app)


def create_test_image():
    img = Image.new("RGB", (100, 100), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


def test_upload_image():
    test_image = create_test_image()
    response = client.post(
        "/upload_image",
        files={"file": ("test.jpg", test_image, "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.json()["filename"] == "test.jpg"


def test_process_image_grayscale():
    test_image = create_test_image()
    response = client.post(
        "/process_image?processing_type=Grayscale",
        files={"file": ("test.jpg", test_image, "image/jpeg")}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"


def test_process_image_invalid_format():
    fake_file = io.BytesIO(b"this is not a real image")
    response = client.post(
        "/process_image?processing_type=Grayscale",
        files={"file": ("fake.txt", fake_file, "text/plain")}
    )
    assert response.status_code == 200
    assert "error" in response.json()