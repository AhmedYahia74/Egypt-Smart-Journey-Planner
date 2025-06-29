from rapidfuzz import fuzz
from config_helper import get_db_params
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict
import logging
import psycopg2
from .db_manager import db_manager

router = APIRouter()
logger = logging.getLogger(__name__)

class HotelRequest(BaseModel):
    city_name: str
    duration: int
    budget: float
    facilities: List[str]

class HotelResponse(BaseModel):
    hotel_id: int
    hotel_name: str
    longitude: float
    latitude: float
    facilities: List[str]
    score: float
    price_per_night: float
    img: str = None

async def get_facilities_ids(conn, user_facilities: List[str]) -> Dict[str, int]:
    """Get facility IDs based on user preferences."""
    try:
        with conn.cursor() as cur:
            # Get all facilities in one query
            cur.execute("""
                        SELECT facility_id, name
                        FROM hotel_facilities
                        WHERE name IS NOT NULL
                        """)
            facilities = cur.fetchall()

            if not facilities:
                logger.error("No facilities found in database")
                raise HTTPException(status_code=500, detail="No facilities available")

            facilities_dic = {}
            for user_facility in user_facilities:
                for f_id, name in facilities:
                    if fuzz.ratio(user_facility.lower(), name.lower()) >= 60:
                        facilities_dic[user_facility] = f_id
                        break

            return facilities_dic
    except psycopg2.Error as e:
        logger.error(f"Database error in get_facilities_ids: {str(e)}")
        raise HTTPException(status_code=500, detail="Error accessing facilities")
    except Exception as e:
        logger.error(f"Unexpected error in get_facilities_ids: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing facilities")

async def get_facilities(conn, hotel_id: int) -> List[str]:
    """Get all hotel facilities from the database."""
    try:
        with conn.cursor() as cur:
            cur.execute("""
                        SELECT hf.facility_id, hf.name
                        FROM hotel_facilities hf
                                 JOIN hotels_facilities_rel hfr ON hf.facility_id = hfr.facility_id
                        WHERE hfr.hotel_id = %s
                        """, (hotel_id,))
            facilities = cur.fetchall()

            if not facilities:
                logger.error(f"No facilities found for hotel ID {hotel_id}")
                return []

            facilities_list = [facility[1] for facility in facilities if facility[1] is not None]
            return facilities_list
    except psycopg2.Error as e:
        logger.error(f"Database error in get_facilities: {str(e)}")
        raise HTTPException(status_code=500, detail="Error accessing hotel facilities")
    except Exception as e:
        logger.error(f"Unexpected error in get_facilities: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing hotel facilities")

def calculate_price_score(user_budget: float, hotel_price: float, duration: int) -> float:
    """Calculate price compatibility score."""
    if user_budget <= 0 or hotel_price <= 0:
        return 0.5
    
    total_hotel_cost = hotel_price * duration
    budget_ratio = total_hotel_cost / user_budget
    
    if budget_ratio <= 0.8:  # Hotel is under budget
        return 1.0
    elif budget_ratio <= 1.0:  # Hotel fits within budget
        return 0.9
    elif budget_ratio <= 1.2:  # Hotel is slightly over budget
        return 0.6
    else:  # Hotel is significantly over budget
        return 0.2

@router.post("/recommend", response_model=Dict[str, List[HotelResponse]])
async def get_hotels(request: HotelRequest):
    """Search for hotels based on city, budget, and preferred facilities."""
    try:
        logger.info(f"Searching hotels in {request.city_name} with facilities: {request.facilities}")

        async with db_manager.get_connection() as conn:
            # Get facility IDs
            facilities_ids = await get_facilities_ids(conn, request.facilities)
            if not facilities_ids:
                raise HTTPException(
                    status_code=400,
                    detail="No matching facilities found"
                )

            # Calculate price limit
            price_limit = request.budget / request.duration

            # Get hotels
            with conn.cursor() as cur:
                query = """
                        SELECT h.hotel_id, \
                               h.name, \
                               MIN(r.total_price)             as price_per_night, \
                               h.longitude, \
                               h.latitude, \
                               array_agg(DISTINCT hf.name)    as facilities, \
                               COUNT(DISTINCT hf.facility_id) as matching_facilities, \
                               h.img
                        FROM hotels h
                                 JOIN hotels_facilities_rel hfr ON h.hotel_id = hfr.hotel_id
                                 JOIN hotel_facilities hf ON hfr.facility_id = hf.facility_id
                                 JOIN rooms r ON h.hotel_id = r.hotel_id
                                 JOIN states s ON h.state_id = s.state_id
                        WHERE lower(s.name) LIKE %s
                          AND hf.facility_id = ANY (%s)
                          AND r.total_price <= %s
                        GROUP BY h.hotel_id, h.name, h.longitude, h.latitude, h.img
                        HAVING COUNT(DISTINCT hf.facility_id) > 0
                        ORDER BY matching_facilities DESC, price_per_night ASC
                        LIMIT 15; \
                        """
                try:
                    cur.execute(query,
                                ('%' + request.city_name.lower() + '%', list(facilities_ids.values()), price_limit))
                    result = cur.fetchall()
                except psycopg2.Error as e:
                    logger.error(f"Database error in hotel query: {str(e)}")
                    raise HTTPException(status_code=500, detail="Error searching for hotels")

            if not result:
                raise HTTPException(
                    status_code=404,
                    detail=f"No hotels found in {request.city_name}"
                )


            # Format response
            hotels = []
            for hotel in result:
                # Get facilities for each hotel
                facilities = await get_facilities(conn, hotel[0])
                facility_score = hotel[6] / len(facilities_ids) 
                price_score = calculate_price_score(request.budget, hotel[2], request.duration)
                # Calculate final score (70% facilities, 30% price)
                final_score = (facility_score * 0.7) + (price_score * 0.3)
                
                hotels.append({
                    'hotel_id': hotel[0],
                    'hotel_name': hotel[1],
                    'price_per_night': hotel[2],
                    'longitude': hotel[3],
                    'latitude': hotel[4],
                    'facilities': facilities,
                    'score': final_score,
                    'img': hotel[7]
                })

            hotels.sort(key=lambda x: x['score'], reverse=True)
            
            # Return top 10 with best overall scores
            top_hotels = hotels[:10]

            return {"hotels": top_hotels}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred"
        )