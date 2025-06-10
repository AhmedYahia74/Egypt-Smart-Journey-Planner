from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config_helper import get_api_urls

# Import all the routers
from .cities_api import router as cities_router
from .hotels_api import router as hotels_router
from .activities_api import router as activities_router
from .plans_api import router as plans_router
from .landmarks_api import router as landmarks_router

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers with their prefixes
app.include_router(cities_router, prefix="/api/cities", tags=["Cities"])
app.include_router(hotels_router, prefix="/api/hotels", tags=["Hotels"])
app.include_router(activities_router, prefix="/api/activities", tags=["Activities"])
app.include_router(plans_router, prefix="/api/plans", tags=["Plans"])
app.include_router(landmarks_router, prefix="/api/landmarks", tags=["Landmarks"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002) 