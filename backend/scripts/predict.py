import tensorflow as tf
import numpy as np
from PIL import Image
import json

# -----------------------------
# Load model
# -----------------------------
model = tf.keras.models.load_model("dishgenie_cnn.keras")

# -----------------------------
# Load class names
# -----------------------------
with open("dishgenie_classes.json", "r") as f:
    raw_classes = json.load(f)
    if isinstance(raw_classes, dict):
        class_names = [k for k, v in sorted(raw_classes.items(), key=lambda x: int(x[1]))]
    else:
        class_names = raw_classes

print("Model loaded successfully!")
print("Classes:", class_names)

# -----------------------------
# Load image
# -----------------------------
image_path = "test.jpg"

image = Image.open(image_path).convert("RGB")
image = image.resize((224, 224))

# Convert to numpy
image_array = np.array(image)

# Add batch dimension
image_array = np.expand_dims(image_array, axis=0)

# IMPORTANT:
# Do NOT divide by 255 here.
# Your model already has a Rescaling(1/255) layer.

# -----------------------------
# Prediction
# -----------------------------
predictions = model.predict(image_array, verbose=0)

predicted_index = np.argmax(predictions[0])
predicted_class = class_names[predicted_index]
confidence = predictions[0][predicted_index] * 100

print()
print("Prediction:", predicted_class)
print(f"Confidence: {confidence:.2f}%")