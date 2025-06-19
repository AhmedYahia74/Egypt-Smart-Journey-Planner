from typing import List, Dict, Any
import aiohttp
from pydantic import BaseModel, Field
from config_helper import get_db_params, get_api_urls
from fastapi import APIRouter, HTTPException
import psycopg2
import json
import logging
from contextlib import asynccontextmanager

router = APIRouter()
logger = logging.getLogger(__name__)

EMBEDDING_API_URL = get_api_urls().get('embedding')
DB_Prams = get_db_params()

# Define common features and their keywords with weights
FEATURES = {
    'sea': {
        'keywords': ['sea', 'beach', 'coast', 'shore', 'ocean', 'mediterranean', 'red sea', 'marine', 'waterfront', 'seaside'],
        'weight': 1.5  # Higher weight for sea-related features
    },
    'desert': {
        'keywords': ['desert', 'sahara', 'sand', 'oasis', 'dunes', 'arid', 'dry'],
        'weight': 1.2
    },
    'historical': {
        'keywords': ['historical', 'ancient', 'pharaonic', 'temple', 'pyramid', 'museum', 'antique', 'heritage', 'ruins', 'archaeological'],
        'weight': 1.3
    },
    'modern': {
        'keywords': ['modern', 'city', 'urban', 'metropolitan', 'contemporary', 'developed', 'quiet', 'peaceful', 'calm', 'serene'],
        'weight': 1.1
    },
    'nature': {
        'keywords': ['nature', 'garden', 'park', 'river', 'nile', 'green', 'scenic', 'landscape', 'outdoor', 'wildlife'],
        'weight': 1.2
    },
    'religious': {
        'keywords': ['mosque', 'church', 'religious', 'spiritual', 'sacred', 'holy', 'pilgrimage', 'worship'],
        'weight': 1.1
    },
    'cultural': {
        'keywords': ['cultural', 'art', 'music', 'festival', 'tradition', 'local', 'custom', 'heritage', 'folklore'],
        'weight': 1.2
    },
    'adventure': {
        'keywords': ['adventure', 'sports', 'activity', 'exciting', 'thrilling', 'diving', 'snorkeling', 'hiking', 'exploring'],
        'weight': 1.3
    },
    'luxury': {
        'keywords': ['luxury', 'upscale', 'premium', 'high-end', 'exclusive', 'resort', 'spa', 'golf', 'yacht'],
        'weight': 1.2
    },
    'family': {
        'keywords': ['family', 'children', 'kids', 'friendly', 'safe', 'playground', 'entertainment', 'suitable'],
        'weight': 1.1
    }
}

class CityRequest(BaseModel):
    city_description: str

class CityResponse(BaseModel):
    name: str
    description: str
    longitude: float 
    latitude: float
    matched_features: List[Dict[str, Any]] = []  # List of matched features with their weights
    match_score: float = 0.0  # Overall match score

def extract_features(text: str) -> List[Dict[str, Any]]:
    """Extract relevant features from the text with their weights."""
    text = text.lower()
    found_features = []
    
    # Check for each feature and its keywords
    for feature, data in FEATURES.items():
        matched_keywords = []
        for keyword in data['keywords']:
            if keyword in text:
                matched_keywords.append(keyword)
        
        if matched_keywords:
            found_features.append({
                'name': feature,
                'weight': data['weight'],
                'matched_keywords': matched_keywords
            })
    
    return found_features

@asynccontextmanager
async def get_db_connection():
    """Create and manage a database connection."""
    conn = None
    try:
        conn = psycopg2.connect(**DB_Prams)
        yield conn
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database connection failed")
    finally:
        if conn:
            conn.close()

async def get_embedding(text: str) -> List[float]:
    """Get embedding for text using the embedding API."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                EMBEDDING_API_URL,
                json={"text": text},
                timeout=10
            ) as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to get embedding from embedding service"
                    )
                
                result = await response.json()
                if "embedding" not in result:
                    raise HTTPException(
                        status_code=500,
                        detail="Invalid embedding response format"
                    )
                return result["embedding"]
    except aiohttp.ClientTimeout:
        raise HTTPException(
            status_code=504,
            detail="Embedding service timeout"
        )
    except aiohttp.ClientError as e:
        logger.error(f"Embedding API error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error calling embedding service"
        )

@router.post("/recommend", response_model=Dict[str, List[CityResponse]])
async def get_cities(request: CityRequest):
    """
    Search for cities based on description and features.
   
    """
    try:
        # Extract features from the description
        features = extract_features(request.city_description)
        logger.info(f"Extracted features: {features}")
        
        # Get the user messages embedding
        user_msgs_embedding = await get_embedding(request.city_description)
        
        # Base query with semantic similarity
        base_query = """
            WITH city_scores AS (
                SELECT 
                    name, 
                    description,
                    longitude,
                    latitude,
                    1 - (embedding <=> %s::vector) AS semantic_similarity,
                    CASE 
        """
        
        # Add feature-based scoring
        if features:
            feature_conditions = []
            for feature in features:
                feature_name = feature['name']
                weight = feature['weight']
                keywords = FEATURES[feature_name]['keywords']
                keyword_conditions = " OR ".join([f"description ILIKE %s OR name ILIKE %s" for _ in keywords])
                feature_conditions.append(f"WHEN ({keyword_conditions}) THEN {weight}")
            base_query += "\n".join(feature_conditions)
        else:
            base_query += "WHEN 1=1 THEN 1"
            
        base_query += """
                    ELSE 1
                    END as feature_score
                FROM states
            )
            SELECT 
                name,
                description,
                longitude,
                latitude,
                (semantic_similarity * 0.7 + feature_score * 0.3) as combined_score
            FROM city_scores
            ORDER BY combined_score DESC
            LIMIT 3
        """
        
        # Prepare parameters for the query
        params = [user_msgs_embedding]
        if features:
            for feature in features:
                feature_name = feature['name']
                keywords = FEATURES[feature_name]['keywords']
                for keyword in keywords:
                    params.extend([f'%{keyword}%', f'%{keyword}%'])
        
        async with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Execute the query
                cur.execute(base_query, params)
                cities = cur.fetchall()

                if not cities:
                    return {"top_cities": []}
                
                # For each city, find which features matched
                cities_list = []
                for city in cities:
                    city_name = city[0]
                    city_desc = city[1]
                    matched_features = []
                    
                    # Check which features match this city
                    for feature in features:
                        feature_name = feature['name']
                        keywords = FEATURES[feature_name]['keywords']
                        matched_keywords = [k for k in keywords if k.lower() in city_desc.lower() or k.lower() in city_name.lower()]
                        if matched_keywords:
                            matched_features.append({
                                'name': feature_name,
                                'weight': feature['weight'],
                                'matched_keywords': matched_keywords
                            })
                    
                    cities_list.append({
                        "name": city_name,
                        "description": city_desc,
                        "longitude": city[2],
                        "latitude": city[3],
                        "matched_features": matched_features,
                        "match_score": float(city[4])  # combined_score from the query
                    })
                
                return {"top_cities": cities_list}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_cities: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing your request"
        )




