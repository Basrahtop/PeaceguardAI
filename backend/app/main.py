from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # Added for CORS
from backend.app.api.v1 import endpoints_text_analysis
from backend.app.api.v1 import endpoints_audio_stream
from backend.app.api.v1 import endpoints_ews
from backend.app.api.v1 import endpoints_live_analysis
from backend.app.config import settings
# This import will trigger the schemas/__init__.py and model rebuilding
from backend.app import schemas # Ensures schemas.__init__.py is run

app = FastAPI(
    title=settings.APP_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# --- CORS Configuration ---
# Define allowed origins. Replace "YOUR_GRADIO_SPACE_URL_HERE" with your actual
# deployed Gradio Space URL once you have it.
# Example: "https://yourusername-yourspacename.hf.space"
origins = [
    "http://localhost:7860",  # For local Gradio development
    "http://127.0.0.1:7860", # Also for local Gradio
    "YOUR_GRADIO_SPACE_URL_HERE", # Placeholder for your deployed Gradio app
    # Add any other origins if needed, e.g., a custom domain for your frontend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True, # Allows cookies, authorization headers, etc.
    allow_methods=["*"],    # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],    # Allows all headers
)
# --- End of CORS Configuration ---

# Include routers
app.include_router(endpoints_text_analysis.router, prefix=settings.API_V1_STR + "/misinformation", tags=["Text Misinformation Analysis"])
app.include_router(endpoints_audio_stream.router, prefix=settings.API_V1_STR + "/audio", tags=["Audio File Analysis"])
app.include_router(endpoints_ews.router, prefix=settings.API_V1_STR + "/ews", tags=["Early Warning System Utilities"])
app.include_router(endpoints_live_analysis.router, prefix=settings.API_V1_STR + "/live", tags=["Live Conversation Analysis"])

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": f"Welcome to {settings.APP_NAME}. Visit /docs for API documentation."}

# To run (from peaceguard_ai directory, venv active):
# For development with reload: uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
# For production (example using Gunicorn, from Dockerfile or Render start command):
# gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend.app.main:app --host 0.0.0.0 --port $PORT