import onnxruntime as ort
import os

MODEL_PATH = "model/inceptionv3_tomato.onnx"
session = None

def load_model():
    global session
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"Model not found at {MODEL_PATH}. "
            f"Please place inceptionv3_tomato.onnx in model/ folder."
        )
    print("Loading ONNX model...")
    session = ort.InferenceSession(
        MODEL_PATH,
        providers=["CPUExecutionProvider"]
    )
    print("Model loaded successfully!")
    # Debug - print all input details
    for i, inp in enumerate(session.get_inputs()):
        print(f"Input {i}:")
        print(f"  Name: {inp.name}")
        print(f"  Shape: {inp.shape}")
        print(f"  Type: {inp.type}")
    return session

def get_session():
    global session
    if session is None:
        load_model()
    return session
