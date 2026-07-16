import numpy as np
import os
import json
import logging

# Get the directory where this file lives
MODEL_DIR = os.path.dirname(os.path.abspath(__file__))

# Lazy-load the model to avoid crashing at import if tensorflow is missing
_model = None


def _load_model():
    global _model
    if _model is not None:
        return _model
    
    from tensorflow.keras.models import model_from_json

    json_path = os.path.join(MODEL_DIR, "new1model_architecture.json")
    weights_path = os.path.join(MODEL_DIR, "new1model_weights.h5")

    with open(json_path, "r") as f:
        loaded_model_json = f.read()

    _model = model_from_json(loaded_model_json)
    _model.load_weights(weights_path)
    logging.info("TensorFlow model loaded successfully.")
    return _model

from .dict import return_disease, show, get_dict

# Function to predict the class of an image
def predict_image_class(image_path):
    try:
        model = _load_model()
    except Exception as e:
        return {"error": f"Model Load Error: {str(e)}"}

    try:
        from tensorflow.keras.utils import load_img, img_to_array

        img = load_img(image_path, target_size=(160, 160))
        img_array = img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array /= 255.0  # Normalize the image

        predictions = model.predict(img_array)

        class_idx = int(np.argmax(predictions[0]))
        confidence = float(predictions[0][class_idx])
        logging.info(f"Predicted class index: {class_idx}, confidence: {confidence:.2f}")

        # The model will return its highest confidence prediction.
        # Removed strict confidence threshold so it always predicts something.
        # This prevents generic "Could not identify" errors on real but blurry leaves.

        # These keys MUST match exactly what get_dict() expects
        class_labels = [
            "Downey Mildew",                        # index 0
            "Pepper__bell___Bacterial_spot",        # index 1
            "Pepper__bell___healthy",               # index 2
            "Tomato__Tomato_YellowLeaf__Curl_Virus",# index 3
            "Tomato_healthy",                       # index 4
        ]

        disease_type = class_labels[class_idx]
        logging.info(f"Disease type: {disease_type}")

        if disease_type in (
            "Tomato_healthy",
            "Pepper__bell___healthy",
        ):
            print("Given plant is a healthy plant")
            return "healthy"
        else:
            output_dict = get_dict(disease_type)
            return output_dict
    except Exception as e:
        logging.error(f"Prediction failed: {e}")
        return {"error": f"Internal Model Error: {str(e)}"}
