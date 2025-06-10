from typing import List
import requests
from pydantic import BaseModel
from config_helper import get_db_params, get_api_urls
from fastapi import APIRouter, HTTPException
import psycopg2
import re
import json

router = APIRouter()

EMBEDDING_API_URL = get_api_urls().get('embedding')
DB_Prams = get_db_params()

# Define common features and their keywords with weights
FEATURES = {
    'sea': {
        'keywords': ['sea', 'beach', 'coast', 'shore', 'ocean', 'mediterranean', 'red sea'],
        'weight': 1.5  # Higher weight for sea-related features
    },
    'desert': {
        'keywords': ['desert', 'sahara', 'sand', 'oasis'],
        'weight': 1.2
    },
    'historical': {
        'keywords': ['historical', 'ancient', 'pharaonic', 'temple', 'pyramid', 'museum'],
        'weight': 1.3
    },
    'modern': {
        'keywords': ['modern', 'city', 'urban', 'metropolitan'],
        'weight': 1.1
    },
    'nature': {
        'keywords': ['nature', 'garden', 'park', 'river', 'nile'],
        'weight': 1.2
    },
    'religious': {
        'keywords': ['mosque', 'church', 'religious', 'spiritual'],
        'weight': 1.1
    }
}

class CityRequest(BaseModel):
    city_description: str
    city_features: List[str] = []

def extract_features(text: str) -> list:
    """Extract relevant features from the text with their weights."""
    text = text.lower()
    found_features = []
    for feature, data in FEATURES.items():
        if any(keyword in text for keyword in data['keywords']):
            found_features.append({
                'name': feature,
                'weight': data['weight']
            })
    return found_features

@router.post("/search")
async def get_cities(request: CityRequest):
    try:
        city_description = request.city_description
        if not city_description:
            raise HTTPException(status_code=400, detail="City description cannot be empty")
            
        conn = None
        cur = None
        try:
            conn = psycopg2.connect(**DB_Prams)
            cur = conn.cursor()
            
            # Extract features from the description
            features = extract_features(city_description)
            
            # Get the user messages embedding
            embedding_response = requests.post(EMBEDDING_API_URL, json={"text": city_description})
            
            if embedding_response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to get embedding from embedding service")
            
            try:
                user_msgs_embedding = embedding_response.json()
                if "embedding" not in user_msgs_embedding:
                    raise HTTPException(status_code=500, detail="Invalid embedding response format")
            except json.JSONDecodeError:
                raise HTTPException(status_code=500, detail="Invalid JSON response from embedding service")
            
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
            params = [user_msgs_embedding["embedding"]]
            if features:
                for feature in features:
                    feature_name = feature['name']
                    keywords = FEATURES[feature_name]['keywords']
                    for keyword in keywords:
                        params.extend([f'%{keyword}%', f'%{keyword}%'])
            
            # Execute the query
            cur.execute(base_query, params)
            cities = cur.fetchall()

            if len(cities) < 3:
                return {"top_cities": [], "message": "No cities found matching your description"}
            
            cities_list = [{
                "name": city[0],
                "description": city[1],
                "longitude": city[2],
                "latitude": city[3],
            } for city in cities]
            
            return {"top_cities": cities_list}

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




