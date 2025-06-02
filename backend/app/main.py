from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # For enabling CORS
from backend.app.api.v1 import endpoints_text_analysis
from backend.app.api.v1 import endpoints_audio_stream   # For audio file uploads
from backend.app.api.v1 import endpoints_ews            # For Early Warning System utilities
# from backend.app.api.v1 import endpoints_live_analysis # Live analysis endpoint is excluded for this deployment
from backend.app.config import settings
from backend.app import schemas # Ensures schemas.__init__.py is run to rebuild Pydantic models

app = FastAPI(
    title=settings.APP_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json" # Path for OpenAPI schema (API docs)
)

# --- CORS Configuration ---
# List of allowed origins (your frontend URLs)
origins = [
    "http://localhost:7860",        # For local Gradio development
    "http://127.0.0.1:7860",       # Also for local Gradio development
    "https://peaceguard-ui.onrender.com",  # YOUR NEWLY DEPLOYED GRADIO FRONTEND URL
    # You can add other frontend URLs here if needed in the future
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          # Allows specific origins
    allow_credentials=True,         # Allows cookies, authorization headers, etc.
    allow_methods=["*"],            # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],            # Allows all headers
)
# --- End of CORS Configuration ---

# Include routers for your different services
app.include_router(
    endpoints_text_analysis.router,
    prefix=settings.API_V1_STR + "/misinformation", 
    tags=["Text Misinformation Analysis"] 
)

app.include_router(
    endpoints_audio_stream.router,
    prefix=settings.API_V1_STR + "/audio",
    tags=["Audio File Analysis"] # Covers STT and subsequent text analysis
)

app.include_router(
    endpoints_ews.router,
    prefix=settings.API_V1_STR + "/ews",
    tags=["Early Warning System Utilities"] # For mock SMS test, etc.
)

# The /live/analyze-segment endpoint and its router (endpoints_live_analysis) 
# are intentionally excluded for this deployment to focus on stable services.

# Root endpoint
@app.get("/", tags=["Root"])
async def read_root():
    return {"message": f"Welcome to {settings.APP_NAME} API. Visit /docs for API documentation."}

# To run this application locally (from the `peaceguard_ai` directory, with venv active):
# uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
#
# For production deployment (example using Gunicorn, often handled by PaaS like Render):
# gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend.app.main:app --host 0.0.0.0 --port $PORT