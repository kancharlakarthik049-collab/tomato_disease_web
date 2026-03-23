import numpy as np
from PIL import Image as PILImage
from utils.model_loader import get_session
from utils.preprocessor import preprocess_image

HIGH_CONFIDENCE = 70.0
LOW_CONFIDENCE = 45.0

CLASS_NAMES = [
    "Tomato_Bacterial_Spot",
    "Tomato_Early_Blight",
    "Tomato_Late_Blight",
    "Tomato_Leaf_Mold",
    "Tomato_Septoria_Leaf_Spot",
    "Tomato_Spider_Mites",
    "Tomato_Target_Spot",
    "Tomato_Tomato_Yellow_Leaf_Curl_Virus",
    "Tomato_Tomato_mosaic_virus",
    "Tomato_healthy"
]

DISEASE_INFO = {
    "Tomato_Bacterial_Spot": {
        "display_name": "Bacterial Spot",
        "description": "Caused by Xanthomonas bacteria affecting leaves and fruits.",
        "symptoms": ["Dark water-soaked spots", "Yellow halos around spots", "Fruit lesions"],
        "treatment": ["Apply copper-based bactericide", "Remove infected leaves", "Avoid overhead watering"],
        "prevention": ["Use disease-free seeds", "Crop rotation", "Proper plant spacing"]
    },
    "Tomato_Early_Blight": {
        "display_name": "Early Blight",
        "description": "Caused by Alternaria solani fungus affecting older leaves first.",
        "symptoms": ["Brown spots with target rings", "Yellow surrounding tissue", "Lower leaves affected first"],
        "treatment": ["Apply fungicide", "Remove infected leaves", "Improve air circulation"],
        "prevention": ["Mulching", "Avoid wetting leaves", "Crop rotation"]
    },
    "Tomato_Late_Blight": {
        "display_name": "Late Blight",
        "description": "Caused by Phytophthora infestans, a destructive water mold.",
        "symptoms": ["Water-soaked spots", "White mold on undersides", "Brown lesions on stems"],
        "treatment": ["Apply fungicide immediately", "Remove infected plants", "Improve drainage"],
        "prevention": ["Plant resistant varieties", "Avoid overhead irrigation", "Monitor humidity"]
    },
    "Tomato_Leaf_Mold": {
        "display_name": "Leaf Mold",
        "description": "Caused by Passalora fulva fungus in high humidity conditions.",
        "symptoms": ["Yellow spots on upper leaf", "Olive-green mold below", "Leaves curl and drop"],
        "treatment": ["Reduce humidity", "Apply fungicide", "Improve ventilation"],
        "prevention": ["Space plants properly", "Avoid leaf wetness", "Use resistant varieties"]
    },
    "Tomato_Septoria_Leaf_Spot": {
        "display_name": "Septoria Leaf Spot",
        "description": "Caused by Septoria lycopersici fungus, very common in wet weather.",
        "symptoms": ["Small circular spots", "Dark borders with light centers", "Tiny black dots in spots"],
        "treatment": ["Remove infected leaves", "Apply fungicide", "Avoid splashing water"],
        "prevention": ["Crop rotation", "Mulching", "Stake plants for airflow"]
    },
    "Tomato_Spider_Mites": {
        "display_name": "Spider Mites",
        "description": "Tiny arachnids that suck plant juices causing leaf damage.",
        "symptoms": ["Tiny yellow dots on leaves", "Fine webbing on plant", "Leaves turn bronze"],
        "treatment": ["Apply miticide", "Spray with water", "Use neem oil"],
        "prevention": ["Keep plants watered", "Avoid dusty conditions", "Introduce predatory mites"]
    },
    "Tomato_Target_Spot": {
        "display_name": "Target Spot",
        "description": "Caused by Corynespora cassiicola fungus in warm humid conditions.",
        "symptoms": ["Circular spots with rings", "Brown lesions on leaves", "Fruit rot possible"],
        "treatment": ["Apply fungicide", "Remove plant debris", "Improve air circulation"],
        "prevention": ["Crop rotation", "Avoid dense planting", "Reduce humidity"]
    },
    "Tomato_Tomato_Yellow_Leaf_Curl_Virus": {
        "display_name": "Yellow Leaf Curl Virus",
        "description": "Viral disease spread by whiteflies, no chemical cure available.",
        "symptoms": ["Yellowing leaf edges", "Upward leaf curling", "Stunted plant growth"],
        "treatment": ["Remove infected plants", "Control whiteflies with insecticide", "No cure available"],
        "prevention": ["Use resistant varieties", "Control whitefly population", "Use reflective mulch"]
    },
    "Tomato_Tomato_mosaic_virus": {
        "display_name": "Mosaic Virus",
        "description": "Viral disease causing mosaic patterns, spread by contact.",
        "symptoms": ["Mosaic yellow-green pattern", "Distorted leaves", "Stunted growth"],
        "treatment": ["Remove infected plants", "Disinfect tools", "No chemical cure"],
        "prevention": ["Use virus-free seeds", "Control aphids", "Wash hands before handling"]
    },
    "Tomato_healthy": {
        "display_name": "Healthy Plant",
        "description": "Your tomato plant appears to be completely healthy!",
        "symptoms": ["No disease symptoms detected"],
        "treatment": ["Continue regular care", "Maintain watering schedule", "Monitor regularly"],
        "prevention": ["Regular inspection", "Proper fertilization", "Good drainage"]
    }
}


def predict_disease(image_path):
    session = get_session()
    img_array = preprocess_image(image_path)
    input_name = session.get_inputs()[0].name
    print(f"Running prediction on preprocessed image...")
    print(f"Input shape: {img_array.shape}")
    outputs = session.run(None, {input_name: img_array})
    raw_output = outputs[0][0]

    print(f"[PREDICTOR] Raw output sum: {np.sum(raw_output):.4f}")
    print(f"[PREDICTOR] Raw output: {raw_output}")

    if abs(float(np.sum(raw_output)) - 1.0) > 0.01:
        e_x = np.exp(raw_output - np.max(raw_output))
        predictions = e_x / e_x.sum()
        print("[PREDICTOR] Applied softmax (model was outputting logits)")
    else:
        predictions = raw_output
        print("[PREDICTOR] Using raw output directly (model outputs probabilities)")

    print("[PREDICTOR] All class scores:")
    for i, (name, prob) in enumerate(zip(CLASS_NAMES, predictions)):
        print(f"  {i}: {name}: {prob * 100:.2f}%")

    class_idx = int(np.argmax(predictions))
    confidence = float(np.max(predictions)) * 100
    disease_name = CLASS_NAMES[class_idx]
    disease_data = DISEASE_INFO.get(disease_name, {})

    print(f"[PREDICTOR] Predicted: {disease_name} ({confidence:.2f}%)")

    top3_indices = np.argsort(predictions)[::-1][:3]
    top3 = [
        {
            "disease": DISEASE_INFO.get(CLASS_NAMES[i], {}).get("display_name", CLASS_NAMES[i]),
            "confidence": round(float(predictions[i]) * 100, 2)
        }
        for i in top3_indices
    ]

    if confidence >= HIGH_CONFIDENCE:
        return {
            "status": "success",
            "confidence_level": "high",
            "confidence_label": "\U0001F7E2 High Confidence",
            "confidence_badge": "success",
            "message": None,
            "disease_name": disease_name,
            "display_name": disease_data.get("display_name", disease_name),
            "confidence": round(confidence, 2),
            "description": disease_data.get("description", ""),
            "symptoms": disease_data.get("symptoms", []),
            "treatment": disease_data.get("treatment", []),
            "prevention": disease_data.get("prevention", []),
            "tips": None,
            "top3": top3
        }

    elif confidence >= LOW_CONFIDENCE:
        return {
            "status": "success",
            "confidence_level": "medium",
            "confidence_label": "\U0001F7E1 Medium Confidence",
            "confidence_badge": "warning",
            "message": "\u26a0\ufe0f Medium confidence result. Please verify with an agricultural expert.",
            "disease_name": disease_name,
            "display_name": disease_data.get("display_name", disease_name),
            "confidence": round(confidence, 2),
            "description": disease_data.get("description", ""),
            "symptoms": disease_data.get("symptoms", []),
            "treatment": disease_data.get("treatment", []),
            "prevention": disease_data.get("prevention", []),
            "tips": [
                "Take a closer photo of the affected leaf",
                "Ensure good lighting conditions",
                "Focus on the most affected area",
                "Avoid shadows on the leaf"
            ],
            "top3": top3
        }

    else:
        return {
            "status": "rejected",
            "confidence_level": "low",
            "confidence_label": "\U0001F534 Low Confidence",
            "confidence_badge": "danger",
            "message": f"\u274c Image not recognized as tomato leaf. (Confidence: {confidence:.1f}%)",
            "disease_name": None,
            "confidence": round(confidence, 2),
            "tips": [
                "Upload a clear close-up of tomato leaf",
                "Make sure leaf fills the frame",
                "Use natural daylight",
                "Keep camera steady to avoid blur",
                "Remove background distractions"
            ]
        }
