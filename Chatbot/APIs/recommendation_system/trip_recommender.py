from typing import List, Dict, Any
import numpy as np
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime, date
import aiohttp
import logging
from config_helper import get_api_urls
import asyncio

logger = logging.getLogger(__name__)

class TripRecommender:
    def __init__(self, db_params: Dict[str, Any]):
        """
        Initialize the trip recommender system.
        
        Args:
            db_params (Dict[str, Any]): Database connection parameters
        """
        self.db_params = db_params
        self.embedding_api_url = get_api_urls().get('embedding')
        if not self.embedding_api_url:
            raise ValueError("Embedding API URL not found in configuration")
        
    async def _get_db_connection(self):
        """Create a database connection."""
        try:
            return psycopg2.connect(**self.db_params)
        except Exception as e:
            logger.error(f"Failed to create database connection: {str(e)}")
            raise
    
    async def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for a text using the embedding API."""
        try:
            if not text or not text.strip():
                logger.warning("Empty text provided for embedding")
                return None
                
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.post(
                        self.embedding_api_url,
                        json={"text": text},
                        timeout=10
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            if 'embedding' not in result:
                                logger.error(f"No embedding in response: {result}")
                                return None
                            return result['embedding']
                        else:
                            logger.error(f"Error getting embedding: {response.status}")
                            return None
                except aiohttp.ClientConnectorError as e:
                    logger.error(f"Could not connect to embedding service: {str(e)}")
                    return None
                except asyncio.TimeoutError:
                    logger.error("Embedding API request timed out")
                    return None
                except aiohttp.ClientError as e:
                    logger.error(f"Error calling embedding API: {str(e)}")
                    return None
        except Exception as e:
            logger.error(f"Unexpected error getting embedding: {str(e)}")
            return None
    
    def _extract_conversation_context(self, user_messages: Dict[str, Any]) -> str:
        """Extract relevant context from the entire conversation."""
        if not user_messages:
            return ""
        
        # Combine all user messages into a single context
        context_parts = []
        
        if 'request_trip' in user_messages:
            context_parts.append(user_messages['request_trip'])
        
        if 'state' in user_messages:
            context_parts.append(f"Location: {user_messages['state']}")
        
        if 'budget' in user_messages:
            context_parts.append(f"Budget: {user_messages['budget']}")
        
        if 'duration' in user_messages:
            context_parts.append(f"Duration: {user_messages['duration']}")
        
        if 'arrival_date' in user_messages:
            context_parts.append(f"Arrival: {user_messages['arrival_date']}")

        for key, value in user_messages.items():
            if key not in ['state', 'budget', 'duration', 'arrival_date']:
                context_parts.append(str(value))
        
        return " ".join(context_parts)

    def _get_date(self, arrival_date: str) -> tuple:
        """Convert a date string to a datetime object."""
        try:
            # Handle single date string
            if isinstance(arrival_date, str):
                date_obj = datetime.strptime(arrival_date, '%Y-%m-%d')
                return date_obj, date_obj

            # Handle list of dates
            if isinstance(arrival_date, list):
                if len(arrival_date) == 1:
                    date_obj = datetime.strptime(arrival_date[0], '%Y-%m-%d')
                    return date_obj, date_obj
                elif len(arrival_date) >= 2:
                    start_date = datetime.strptime(arrival_date[0], '%Y-%m-%d')
                    end_date = datetime.strptime(arrival_date[1], '%Y-%m-%d')
                    return start_date, end_date
            
            raise ValueError(f"Invalid date format: {arrival_date}")
        except Exception as e:
            logger.error(f"Error parsing date: {str(e)}")
            raise

    def _calculate_similarity_score(self, user_preferences: Dict[str, Any], user_messages: Dict[str, Any], trip: Dict[str, Any]) -> float:
        """Calculate similarity score between user preferences and a trip."""
        try:
            # Budget compatibility score (0-1)
            budget_score = 1.0
            if 'budget' in user_preferences:
                user_budget = float(user_preferences['budget'])
                trip_price = float(trip['price'])
                if user_budget < trip_price * 0.7:  # If user budget is less than 70% of trip price
                    budget_score = 0.0
                elif user_budget > trip_price * 1.3:  # If user budget is more than 30% above trip price
                    budget_score = 0.5
                else:
                    budget_score = 1.0
            
            # Duration compatibility score (0-1)
            duration_score = 1.0
            if 'duration' in user_preferences and 'duration' in trip:
                try:
                    user_duration = int(user_preferences['duration'])
                    trip_duration = int(trip['duration'].split()[0])
                    if 'Hours' in trip['duration']:
                        trip_duration /= 24
                    duration_diff = abs(user_duration - trip_duration)
                    duration_score = max(0, 1 - (duration_diff / max(user_duration, trip_duration)))
                except (ValueError, IndexError, AttributeError) as e:
                    logger.error(f"Error calculating duration score: {str(e)}")
                    duration_score = 0.5

            # Date compatibility score (0-1)
            date_score = 1.0
            if 'arrival_date' in user_preferences and 'date' in trip:
                try:
                    # Parse trip date
                    trip_date = None
                    if isinstance(trip['date'], str):
                        try:
                            trip_date = datetime.strptime(trip['date'], '%Y-%m-%d')
                        except ValueError:
                            logger.error(f"Invalid trip date format: {trip['date']}")
                            date_score = 0.0
                            return date_score
                    elif isinstance(trip['date'], datetime):
                        trip_date = trip['date']
                    else:
                        logger.error(f"Invalid trip date type: {type(trip['date'])}")
                        date_score = 0.0
                        return date_score

                    # Parse user date
                    try:
                        user_date = datetime.strptime(user_preferences['arrival_date'], '%Y-%m-%d')
                        # Exact date match gets highest score
                        if user_date == trip_date:
                            date_score = 1.0
                        else:
                            # Calculate days difference
                            date_diff = abs((user_date - trip_date).days)
                            # Score decreases as date difference increases
                            # 0 days = 1.0, 1 day = 0.8, 2 days = 0.6, 3 days = 0.4, 4+ days = 0.2
                            date_score = max(0.2, 1.0 - (date_diff * 0.2))
                    except ValueError:
                        logger.error(f"Invalid user date format: {user_preferences['arrival_date']}")
                        date_score = 0.0
                        return date_score
                except Exception as e:
                    logger.error(f"Error calculating date score: {str(e)}")
                    date_score = 0.0
                    return date_score
            
            # Calculate weighted final score with adjusted weights
            weights = {
                'budget': 0.2,
                'duration': 0.15,
                'date': 0.3,  # Increased weight for date matching
                'content': 0.35  # Slightly reduced content weight
            }
            
            try:
                final_score = (
                    budget_score * weights['budget'] +
                    duration_score * weights['duration'] +
                    date_score * weights['date'] +
                    float(trip.get('similarity_score', 0.0)) * weights['content']
                )
                return final_score
            except (ValueError, TypeError, KeyError) as e:
                logger.error(f"Error calculating final score: {str(e)}")
                return 0.0
        except Exception as e:
            logger.error(f"Error calculating similarity score: {str(e)}")
            return 0.0
    
    async def get_recommendations(
        self,
        user_preferences: Dict[str, Any],
        user_messages: Dict[str, Any],
        top_n: int = 3
    ) -> List[Dict[str, Any]]:
        """Get trip recommendations based on user preferences and messages."""
        try:
            logger.info(f"Processing recommendations for preferences: {user_preferences}")
            logger.info(f"User messages: {user_messages}")
            
            # Extract conversation context
            context = self._extract_conversation_context(user_messages)
            if not context:
                logger.warning("Failed to extract conversation context")
                return []
            
            # Get embedding for context
            context_embedding = await self._get_embedding(context)
            if not context_embedding:
                logger.warning("Failed to get embedding for context")
                return []
            
            # Query database with vector similarity
            conn = await self._get_db_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Prepare patterns for state matching
                state = user_preferences.get('state', '').strip()
                exact_pattern = state
                start_pattern = f"{state},%"
                middle_pattern = f"%, {state},%"
                end_pattern = f"%, {state}"
                
                logger.info(f"Executing query with state patterns: {[exact_pattern, start_pattern, middle_pattern, end_pattern]}")
                
                # Check if user specified an exact date
                start_date, end_date = None, None
                if 'arrival_date' in user_preferences:
                    try:
                        start_date, end_date = self._get_date(user_preferences['arrival_date'])
                        logger.info(f"Using date range: {start_date} to {end_date}")
                    except Exception as e:
                        logger.error(f"Error parsing arrival date: {str(e)}")
                
                # Build the query with vector similarity and date filtering
                query = """
                    WITH ranked_trips AS (
                        SELECT 
                            t.*,
                            1 - (t.embedding <=> %s::vector) as similarity_score
                        FROM trips t
                        WHERE t.is_active = true 
                        AND t.available_seats > 0
                        AND (
                            t.state ILIKE %s
                            OR t.state ILIKE %s
                            OR t.state ILIKE %s
                            OR t.state ILIKE %s
                        )
                        AND t.date >= %s AND t.date <= %s
                    )
                    SELECT * FROM ranked_trips
                    ORDER BY similarity_score DESC
                    LIMIT %s
                """
                
                # Get top 10 trips initially for better selection
                initial_limit = 10
                
                params = [
                    context_embedding,
                    exact_pattern,
                    start_pattern,
                    middle_pattern,
                    end_pattern,
                    start_date.strftime('%Y-%m-%d') if start_date else '1970-01-01',
                    end_date.strftime('%Y-%m-%d') if end_date else '2100-12-31',
                    initial_limit
                ]
                
                cur.execute(query, tuple(params))
                
                trips = cur.fetchall()
                logger.info(f"Found {len(trips)} trips in database")
                
                if not trips and start_date:
                    # If no trips found on exact date, try without date filter
                    logger.info("No trips found on exact date, trying without date filter")
                    query = query.replace("AND t.date >= %s AND t.date <= %s", "")
                    params.pop(-3)  # Remove end_date parameter
                    params.pop(-3)  # Remove start_date parameter
                    cur.execute(query, tuple(params))
                    trips = cur.fetchall()
                    logger.info(f"Found {len(trips)} trips without date filter")
                
                if not trips:
                    return []
                
                # Calculate final scores and format recommendations
                recommendations = []
                for trip in trips:
                    trip_dict = dict(trip)
                    
                    # Convert date to string format
                    if isinstance(trip_dict.get('date'), (datetime, date)):
                        trip_dict['date'] = trip_dict['date'].strftime('%Y-%m-%d')
                    
                    # Calculate similarity score
                    similarity_score = self._calculate_similarity_score(
                        user_preferences,
                        user_messages,
                        trip_dict
                    )
                    
                    # Add to recommendations
                    recommendations.append({
                        'trip_id': trip_dict['trip_id'],
                        'title': trip_dict['title'],
                        'description': trip_dict['description'],
                        'state': trip_dict['state'],
                        'price': float(trip_dict['price']),
                        'date': trip_dict['date'],
                        'available_seats': int(trip_dict['available_seats']),
                        'duration': str(trip_dict['duration']),
                        'img': trip_dict.get('img', None),
                        'match_score': float(similarity_score)
                    })
                
                # Sort recommendations by match score
                recommendations.sort(key=lambda x: x['match_score'], reverse=True)
                
                # Return top N recommendations
                top_recommendations = recommendations[:top_n]
                logger.info(f"Returning top {len(top_recommendations)} recommendations from {len(recommendations)} candidates")
                return top_recommendations
                
        except Exception as e:
            logger.error(f"Error getting recommendations: {str(e)}")
            raise
