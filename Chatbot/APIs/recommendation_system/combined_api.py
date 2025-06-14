from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import all the routers
from .cities_api import router as cities_router
from .hotels_api import router as hotels_router
from .activities_api import router as activities_router
from .plans_api import router as plans_router
from .landmarks_api import router as landmarks_router
from .trips_api import router as trips_router

app = FastAPI(title="Egypt Smart Journey Planner API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error handler caught: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again later."}
    )

# Include all routers with their prefixes
app.include_router(cities_router, prefix="/api/cities", tags=["Cities"])
app.include_router(hotels_router, prefix="/api/hotels", tags=["Hotels"])
app.include_router(activities_router, prefix="/api/activities", tags=["Activities"])
app.include_router(plans_router, prefix="/api/plans", tags=["Plans"])
app.include_router(landmarks_router, prefix="/api/landmarks", tags=["Landmarks"])
app.include_router(trips_router, prefix="/api/trips", tags=["Trips"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002) 