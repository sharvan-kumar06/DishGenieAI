import io
import sys
from pathlib import Path

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app


def run_validation():
    print("=" * 60)
    print("DISHGENIE BACKEND INTEGRATION VALIDATION (STEP 6)")
    print("=" * 60)

    client = TestClient(app)

    # 1. Test GET /api/health
    print("\n[1] Testing GET /api/health ...")
    health_res = client.get("/api/health")
    print(f"Status Code: {health_res.status_code}")
    print(f"Response: {health_res.json()}")
    assert health_res.status_code == 200, "Health check failed"
    assert health_res.json()["status"] == "ok"
    assert health_res.json()["services"]["vision"]["available"] is True
    assert health_res.json()["services"]["recipe"]["available"] is True
    print(">>> GET /api/health PASSED (Vision & Recipe services available)!")

    # 2. Test POST /api/vision/predict with an image
    print("\n[2] Testing POST /api/vision/predict with real image data ...")
    test_img_path = Path(__file__).resolve().parent.parent.parent / "test_potato.jpg"
    if not test_img_path.exists():
        test_img_path = Path(__file__).resolve().parent.parent.parent / "test_tomato.jpg"

    if test_img_path.exists():
        with open(test_img_path, "rb") as f:
            image_bytes = f.read()
        filename = test_img_path.name
        content_type = "image/jpeg"
        print(f"Using image from: {test_img_path}")
    else:
        img = Image.new("RGB", (224, 224), color=(220, 40, 30))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        image_bytes = buf.getvalue()
        filename = "test_image.jpg"
        content_type = "image/jpeg"
        print("Using dynamically generated RGB test image")

    files = {"image": (filename, image_bytes, content_type)}
    pred_res = client.post("/api/vision/predict", files=files)
    print(f"Status Code: {pred_res.status_code}")
    print("Prediction Response JSON:", pred_res.json())

    assert pred_res.status_code == 200, f"Predict failed: {pred_res.text}"
    data = pred_res.json()
    assert "prediction" in data
    assert "top_predictions" in data
    assert len(data["top_predictions"]) == 3
    print(">>> POST /api/vision/predict PASSED!")

    # 3. Test POST /api/recipe/generate with local FLAN-T5
    print("\n[3] Testing POST /api/recipe/generate with local FLAN-T5 ...")
    recipe_payload = {
        "ingredients": ["Tomato", "Potato", "Carrot"],
        "preferences": {
            "diet": "Vegetarian",
            "cuisine": "Indian",
            "cookingTime": 30,
            "difficulty": "Easy",
            "servings": 2,
            "additionalIngredients": "onion, garlic",
        },
    }
    print(f"Sending Payload: {recipe_payload}")
    recipe_res = client.post("/api/recipe/generate", json=recipe_payload)
    print(f"Status Code: {recipe_res.status_code}")
    recipe_data = recipe_res.json()
    print("Recipe Response JSON:")
    print(recipe_data)

    assert recipe_res.status_code == 200, f"Recipe generation failed: {recipe_res.text}"
    assert recipe_data.get("success") is True
    assert (recipe_data.get("recipe") is not None) or (recipe_data.get("raw_text") is not None)
    print(">>> POST /api/recipe/generate PASSED!")

    print("\n" + "=" * 60)
    print("ALL STEP 6 BACKEND INTEGRATION TESTS SUCCEEDED!")
    print("=" * 60)


if __name__ == "__main__":
    run_validation()
