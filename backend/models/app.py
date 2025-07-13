import os
import uuid
import asyncio
from quart import Quart, request, jsonify
from quart_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from quart_cors import cors
from pydantic import BaseModel, ValidationError
import torch
from loguru import logger
from ipfs_handler import upload_to_ipfs
from blockchain import store_file_metadata
from auth import register_user, authenticate_user
from dotenv import load_dotenv
from functools import wraps
from collections import defaultdict
from time import time

# Load environment variables from .env
load_dotenv()

app = Quart(__name__)
app = cors(app, allow_origin="*")  # Enable CORS for all origins (adjust in production)

# JWT Setup
app.config['JWT_SECRET_KEY'] = os.getenv("JWT_SECRET_KEY", "super-secret-key")
jwt = JWTManager(app)

# Rate limiting configuration
RATE_LIMITS = {
    "/register": (5, 60),    # 5 requests per 60 seconds
    "/login": (10, 60),      # 10 requests per 60 seconds
    "/upload": (3, 60),      # 3 requests per 60 seconds
    "/recommend": (10, 60),  # 10 requests per 60 seconds
}
client_request_times = defaultdict(list)

def rate_limit(route):
    def decorator(f):
        @wraps(f)
        async def wrapper(*args, **kwargs):
            ip = request.headers.get("X-Forwarded-For", request.remote_addr)
            max_calls, period = RATE_LIMITS.get(route, (10, 60))
            now = time()
            window_start = now - period
            client_request_times[ip] = [t for t in client_request_times[ip] if t > window_start]
            if len(client_request_times[ip]) >= max_calls:
                return jsonify(error=f"Rate limit exceeded. Max {max_calls} calls per {period} seconds."), 429
            client_request_times[ip].append(now)
            return await f(*args, **kwargs)
        return wrapper
    return decorator

# Pydantic models for input validation
class RegisterRequest(BaseModel):
    username: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class RecommendRequest(BaseModel):
    features: list[float]

# AI model loading (if needed)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model_path = os.getenv("MODEL_PATH", "models/trained_advanced_model.pth")

model = None
async def load_model():
    global model
    try:
        from models.federated_model import AdvancedModel
        model = AdvancedModel()
        model.load_state_dict(torch.load(model_path, map_location=device))
        model.eval()
        logger.info(f"AI model loaded on {device}")
    except Exception as e:
        logger.error(f"Failed to load AI model: {e}")

@app.before_serving
async def startup():
    await load_model()

async def ai_infer(features):
    global model
    if model is None:
        raise RuntimeError("Model not loaded")
    tensor = torch.tensor(features, dtype=torch.float32).unsqueeze(0).to(device)
    with torch.no_grad():
        outputs = model(tensor)
        _, predicted = torch.max(outputs, 1)
    return predicted.item()

@app.route("/register", methods=["POST"])
@rate_limit("/register")
async def register():
    try:
        data = RegisterRequest(**await request.get_json())
    except ValidationError as ve:
        return jsonify(error=ve.errors()), 400

    result = await asyncio.to_thread(register_user, data.username, data.password)
    return jsonify(result)

@app.route("/login", methods=["POST"])
@rate_limit("/login")
async def login():
    try:
        data = LoginRequest(**await request.get_json())
    except ValidationError as ve:
        return jsonify(error=ve.errors()), 400

    is_valid = await asyncio.to_thread(authenticate_user, data.username, data.password)
    if is_valid:
        token = create_access_token(identity=data.username)
        return jsonify(token=token)
    else:
        return jsonify(message="Invalid credentials"), 401

@app.route("/upload", methods=["POST"])
@jwt_required
@rate_limit("/upload")
async def upload_file():
    try:
        logger.info("=== /upload route called ===")

        user = get_jwt_identity()  # No await needed here
        logger.info(f"User identity from JWT: {user}")

        # Get the multipart form data (including files)
        form_data = await request.form
        files = await request.files  # This is now properly awaited
        
        logger.info(f"Files keys received: {list(files.keys())}")

        if 'file' not in files:
            logger.error("No file part named 'file' in the request.files")
            return jsonify(error="No file uploaded with key 'file'"), 400

        file = files['file']
        logger.info(f"File object info - filename: '{file.filename}', content_type: '{file.content_type}'")

        if not file.filename:
            logger.error("Uploaded file has an empty filename")
            return jsonify(error="Empty filename"), 400

        temp_dir = "temp"
        os.makedirs(temp_dir, exist_ok=True)
        logger.info(f"Ensured temp directory exists at: {temp_dir}")

        filename = f"{uuid.uuid4()}_{file.filename}"
        filepath = os.path.join(temp_dir, filename)
        logger.info(f"Saving uploaded file to: {filepath}")

        await file.save(filepath)
        logger.info(f"File saved successfully at {filepath}")

        logger.info("Running AI safety check...")
        safe = await asyncio.to_thread(run_ai_file_safety_check, filepath)
        logger.info(f"AI safety check result: {safe}")

        if not safe:
            os.remove(filepath)
            logger.warning(f"File {filepath} rejected by AI safety check and deleted")
            return jsonify(error="File rejected by AI safety check"), 400

        logger.info("Uploading file to IPFS...")
        ipfs_hash = await asyncio.to_thread(upload_to_ipfs, filepath)
        logger.info(f"File uploaded to IPFS with hash: {ipfs_hash}")

        logger.info("Storing file metadata on blockchain...")
        await asyncio.to_thread(store_file_metadata, user, ipfs_hash)
        logger.info(f"Stored metadata for user {user} with IPFS hash {ipfs_hash}")

        logger.info("Generating AI tags for file...")
        tags = await asyncio.to_thread(run_ai_file_tagging, filepath)
        logger.info(f"AI tags generated: {tags}")

        os.remove(filepath)
        logger.info(f"Deleted local file {filepath}")

        logger.info("Upload process completed successfully.")
        return jsonify(ipfs_hash=ipfs_hash, tags=tags)

    except Exception as e:
        logger.error(f"Exception in /upload route: {e}", exc_info=True)
        return jsonify(error="Upload failed due to server error"), 500

@app.route("/recommend", methods=["POST"])
@jwt_required
@rate_limit("/recommend")
async def recommend():
    try:
        data = RecommendRequest(**await request.get_json())
        pred = await ai_infer(data.features)
        return jsonify(recommendation=pred)
    except ValidationError as ve:
        return jsonify(error=ve.errors()), 400
    except Exception as e:
        logger.error(f"AI inference error: {e}")
        return jsonify(error="Internal AI error"), 500

@app.route("/")
async def root():
    return "BlockShareX Backend API Running."

# Dummy AI helper functions
def run_ai_file_safety_check(filepath):
    logger.info(f"AI safety check on {filepath}")
    return True

def run_ai_file_tagging(filepath):
    logger.info(f"AI tagging on {filepath}")
    return ["example-tag1", "example-tag2"]

if __name__ == "__main__":
    app.run(debug=True, port=5000)