import heapq
import requests
from APIs.test_recommendaaation_model import calculate_similarity
from config_helper import get_db_params, get_api_urls
from fastapi import FastAPI, HTTPException
from contextlib import contextmanager
import psycopg2
from pydantic import BaseModel
from typing import List

app = FastAPI()

class PlanRequest(BaseModel):
    city_name: str
    budget: float
    suggested_hotels: List[dict]
    suggested_activities: List[dict]
    suggested_landmarks: List[dict]

def search_optimal_items(budget, activity_landmark_options):
    scale = 100
    max_b= int(budget*scale)+1
    dp=[0]*max_b
    selected_options=[[] for _ in range(max_b)]
    for option in activity_landmark_options:
        price = int(option['price']*scale)
        if price <= 0:
            continue
        for b in range(max_b-1,price-1,-1):
            new_value=dp[b-price]+option['score']
            if new_value>dp[b]:
                dp[b]=new_value
                selected_options[b]=selected_options[b-price]+[option]
    max_value = 0
    max_index = 0
    for i in range(max_b):
        if dp[i]>max_value:
            max_value=dp[i]
            max_index=i
    return max_value,selected_options[max_index]

def seperate_activities_landmarks(selected_options,activities,landmarks):
    activities_options=[item for item in selected_options if item in activities]
    landmarks_options=[item for item in selected_options if item in landmarks]
    return activities_options,landmarks_options
def calculate_similarity(comb1, comb2):
    hotel_overlap = int(comb1['hotel']['hotel_id'] == comb2['hotel']['hotel_id'])
    activity_overlap = len(set(a['id'] for a in comb1['activities']) & set(a['id'] for a in comb2['activities']))
    landmark_overlap = len(set(l['id'] for l in comb1['landmarks']) & set(l['id'] for l in comb2['landmarks']))
    return hotel_overlap + activity_overlap + landmark_overlap



def find_best_plan_options(hotels, activities, landmarks, budget):
   activity_landmark_options = activities + landmarks
   for item_list in activity_landmark_options:
        for key,item in item_list.items():
            if key=='price'and item is None:
                item_list['price'] = 0.0
   best_options = []
   activity_landmark_options.sort(key=lambda x: x['score'], reverse=True)
   for hotel in hotels:
       remaining_budget = budget - hotel['price_per_night']
       if remaining_budget <= 0:
           continue
       options_score,selected_options = search_optimal_items(remaining_budget, activity_landmark_options)
       options_cost=sum( a["price"]for a in selected_options)
       total_cost = options_cost+ hotel['price_per_night']
       total_score = options_score+hotel['score']
       activities_options,landmarks_options=seperate_activities_landmarks(selected_options,activities,landmarks)
       plan_combination = {
           "hotel": hotel,
           "activities": activities_options,
           "landmarks": landmarks_options,
           "total_score": total_score,
           "total_cost": total_cost
       }
       if len(best_options) < 3:
            heapq.heappush(best_options,  (total_score, plan_combination))
       elif total_score > best_options[0][0]:
           heapq.heappushpop(best_options, (total_score,plan_combination))


   suggestion=[item[1] for item in sorted(best_options,key=lambda  x:x[0],reverse=True)]
   
   return suggestion



@app.post("/suggest_plan")
def suggest_plan(request: PlanRequest):
    plan_combinations = find_best_plan_options(
        request.suggested_hotels,
        request.suggested_activities,
        request.suggested_landmarks,
        request.budget
    )
    return {"plan_combinations": plan_combinations}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3003)
