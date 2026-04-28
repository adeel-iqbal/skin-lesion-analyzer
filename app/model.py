import json
import numpy as np
from pathlib import Path
from PIL import Image
import tensorflow as tf
from tensorflow.keras.applications.efficientnet import preprocess_input

BASE = Path(__file__).parent.parent
MODEL_PATH = BASE / "models" / "skin_model.keras"
CLASSES_PATH = BASE / "models" / "classes.json"

with open(CLASSES_PATH) as f:
    _meta = json.load(f)

CLASSES = _meta["classes"]
IDX_TO_CLASS = {int(k): v for k, v in _meta["idx_to_class"].items()}
IMG_SIZE = _meta["img_size"]

CLASS_INFO = {
    "akiec": {"full": "Actinic Keratoses", "risk": "pre-cancerous"},
    "bcc":   {"full": "Basal Cell Carcinoma", "risk": "malignant"},
    "bkl":   {"full": "Benign Keratosis", "risk": "benign"},
    "df":    {"full": "Dermatofibroma", "risk": "benign"},
    "mel":   {"full": "Melanoma", "risk": "malignant"},
    "nv":    {"full": "Melanocytic Nevi", "risk": "benign"},
    "vasc":  {"full": "Vascular Lesion", "risk": "benign"},
}

_model = None

def load_model():
    global _model
    if _model is None:
        _model = tf.keras.models.load_model(MODEL_PATH)
    return _model


def predict(image_path: str) -> dict:
    model = load_model()

    img = Image.open(image_path).convert("RGB").resize((IMG_SIZE, IMG_SIZE))
    arr = np.array(img, dtype=np.float32)
    arr = preprocess_input(arr)
    arr = np.expand_dims(arr, axis=0)

    probs = model.predict(arr, verbose=0)[0]

    top3_idx = probs.argsort()[-3:][::-1]
    top3 = [
        {
            "class": IDX_TO_CLASS[i],
            "full_name": CLASS_INFO[IDX_TO_CLASS[i]]["full"],
            "risk": CLASS_INFO[IDX_TO_CLASS[i]]["risk"],
            "confidence": round(float(probs[i]) * 100, 2),
        }
        for i in top3_idx
    ]

    predicted = top3[0]
    all_scores = {IDX_TO_CLASS[i]: round(float(p) * 100, 2) for i, p in enumerate(probs)}

    return {
        "predicted_class": predicted["class"],
        "full_name": predicted["full_name"],
        "risk": predicted["risk"],
        "confidence": predicted["confidence"],
        "top3": top3,
        "all_scores": all_scores,
    }
