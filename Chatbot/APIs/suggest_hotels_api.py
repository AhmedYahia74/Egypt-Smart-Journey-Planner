from rapidfuzz import fuzz
from config_helper import get_db_params
from fastapi import FastAPI, HTTPException
import psycopg2
from pydantic import BaseModel
from typing import List
import math
app = FastAPI()
DB_Prams = get_db_params()
def best_match_score(query, choices):
    scores = []
    for choice in choices:
        score = max(
            fuzz.ratio(query, choice),
            fuzz.partial_ratio(query, choice),
            fuzz.token_sort_ratio(query, choice),
            fuzz.token_set_ratio(query, choice)
        )
        scores.append((choice, score))
    best = max(scores, key=lambda x: x[1])
    return best

def get_facilities_ids(conn, user_facilities):
    with conn.cursor() as cur:
        select_query = """SELECT facility_id , name from hotel_facilities """
        cur.execute(select_query,)
        facilities_ids = cur.fetchall()
        # search for the facilities in the rooms
        select_query = """SELECT room_facility_id, name FROM room_facilities"""
        cur.execute(select_query)
        room_facilities= cur.fetchall()
        all_facilities =  facilities_ids + room_facilities
        facilities_names = [facility[1] for facility in all_facilities]
        facilities_dic = {}
        # Use fuzzy matching to find the best match for each user facility
        for user_facility in user_facilities:
            match, best_match = best_match_score(user_facility.lower(), [name.lower() for name in facilities_names])
            print(match,best_match, user_facility)
            if  best_match >= 80:
                for f_id, name in all_facilities:
                    if name.lower() == match:
                        facilities_dic[user_facility] = f_id
                        break

        return  facilities_dic



def get_hotels_facilities(conn, city_name, facilities_ids, price_limit_per_night):
    with conn.cursor() as cur:
        select_query = '''SELECT h.hotel_id, h.name, r.total_price,h.longitude,h.latitude,hf.facility_id, hf.name
                          FROM hotels h
                          JOIN hotels_facilities_rel hfr ON h.hotel_id = hfr.hotel_id
                          JOIN hotel_facilities hf ON hfr.facility_id = hf.facility_id
                          JOIN rooms r ON h.hotel_id = r.hotel_id
                          JOIN states s ON h.state_id = s.state_id
                          WHERE lower(s.name) LIKE %s and hf.facility_id = ANY(%s)
                           and r.total_price <= %s limit 10'''
        cur.execute(select_query, ('%' + city_name.lower() + '%',facilities_ids, price_limit_per_night))
        result = cur.fetchall()
        hotels = {}
        for hotel in result:
            if hotel[0] not in hotels:
                hotels[hotel[0]]={
                    "hotel_id": hotel[0],
                    "hotel_name": hotel[1],
                    "price_per_night": hotel[2],
                    "longitude": hotel[3],
                    "latitude": hotel[4],
                    "facilities_ids": set(),
                    "facilities": set()
                }
            hotels[hotel[0]]["facilities_ids"].add(hotel[5])
            hotels[hotel[0]]["facilities"].add(hotel[6])

        return hotels

def calculate_matching_score(hotel_facilities, user_facilities):
    total_user_facilities = len(user_facilities)
    # Calculate the minimum and maximum price for normalization
    prices = [hotel["price_per_night"] for hotel in hotel_facilities.values()
                    if  not math.isnan(hotel["price_per_night"])]
    min_price = min(prices) if prices else 0
    max_price = max(prices) if prices else 0
    alpha= 0.7
    beta=0.3


    for hotel_id,hotel_data in hotel_facilities.items():
        matched_facilities = hotel_data["facilities"].intersection(user_facilities)
        matching_score = len(matched_facilities) / total_user_facilities if total_user_facilities else 0

        # Normalize the price to a score between 0 and 1
        if math.isnan(hotel_data["price_per_night"])  or max_price == min_price:
            normalized_price = 0.0
        else:
            normalized_price = 1 - (hotel_data["price_per_night"] - min_price) / (max_price - min_price)

        # Calculate the final score
        normalized_score= alpha * matching_score + beta * normalized_price

        hotel_data["score"] = normalized_score

    # Sort hotels by matching score in descending order
    sorted_hotels = sorted(hotel_facilities.values(), key=lambda x: x["score"], reverse=True)
    return sorted_hotels




class HotelRequest(BaseModel):
    city_name: str
    duration: int
    budget: float
    user_facilities: List[str]

@app.post("/suggest_hotels")
def suggest_hotels(request: HotelRequest):
    city_name = request.city_name
    user_facilities = request.user_facilities
    conn = None

    try:
        conn = psycopg2.connect(**DB_Prams)
        # get all the hotels in the city with the user preferences
        facilities_ids = get_facilities_ids(conn,user_facilities)
        if not facilities_ids:
            raise HTTPException(status_code=400, detail="No matching facilities found for the provided preferences")
            
        price_limit_per_night = request.budget / request.duration
        hotels_facilitates = get_hotels_facilities(conn, city_name, list(facilities_ids.values()),price_limit_per_night)
        
        if not hotels_facilitates:
            raise HTTPException(status_code=404, detail=f"No hotels found in {city_name} matching your criteria")
            
        # calculate the matching score for each hotel
        sorted_hotels = calculate_matching_score(hotels_facilitates , set(user_facilities))

        hotels = []
        for hotel in sorted_hotels:
            hotel_data = {
                'hotel_id': hotel['hotel_id'],
                "hotel_name": hotel["hotel_name"],
                "longitude": hotel["longitude"],
                "latitude": hotel["latitude"],
                "facilities_ids": list(hotel["facilities_ids"]),
                "facilities": list(hotel["facilities"]),
                "score": hotel["score"]
            }

            # Handle NaN values in price
            if math.isnan(hotel["price_per_night"]):
                hotel_data["price_per_night"] = None
            else:
                hotel_data["price_per_night"] = hotel["price_per_night"]

            hotels.append(hotel_data)
        return {"hotels": hotels}
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3001)