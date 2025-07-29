# Egypt Smart Journey Planner (RAHHAL)

## Overview

Egypt Smart Journey Planner is an intelligent travel planning platform designed to help tourists plan trips to Egypt through an AI-powered conversational chatbot.
The system combines Natural Language Processing (NLP), recommendation algorithms, and a modern web interface to provide personalized travel recommendations, including hotels, activities, landmarks, and complete itineraries.


## Architecture

The project consists of three main components:

### 1. Conversational AI Chatbot (Rasa-based)

A sophisticated chatbot built with Rasa that understands natural language queries about travel preferences and provides intelligent recommendations.
It can handle various travel-related intents, such as:

* Trip planning and suggestions
* Activity and landmark recommendations
* Budget and duration planning
* Hotel feature preferences

### 2. Spring Boot Backend

A robust backend application built with Spring Boot 3.4.3 and Java 21, providing:

* User Management – Tourist and company accounts with JWT authentication
* Trip Management – Companies can create and manage travel packages
* Booking System – Stripe integration for reservations and payments
* Real-Time Communication – WebSocket support for live chat

### 3. Angular Frontend

A modern web application built with Angular 19, featuring:

* Interactive user interface for tourists and travel companies
* Real-time chat integration with STOMP/WebSocket
* Responsive design optimized for desktop and mobile

---

## Key Features

### Intelligent Recommendations

* Cities recommendation based on the user's imaginary journey
* Personalized plan suggestions based on user interests, budget, and travel duration.
* Content-based recommendation using text similarity with SBERT embeddings.
* Multi-level suggestions: cities, Hotels, landmarks, activities, and full trip plans.
* Natural language understanding from user input via chatbot.
* Embedding-based matching between user input and trip/place descriptions.
* Pre-planned trip matching from tourism company posts.

### Conversational Interface

Users can chat naturally with the AI assistant to:

* Specify travel preferences and constraints
* Receive tailored recommendations
* Modify or refine travel plans
* Get details about destinations

### Multi-User Platform

* Tourists – Plan trips, book experiences, and interact with the AI
* Travel Companies – Create and manage trip offerings
* Secure Authentication – JWT-based login system

---

## Technology Stack

| Layer      | Technologies Used                                     |
| ---------- | ----------------------------------------------------- |
| AI/ML      | 	Rasa (NLP, NLU), SBERT (for text embeddings)و FastAPI (recommendation API)                                   |
| Backend    | Spring Boot 3.4.3, Java 21, PostgreSQL, JPA/Hibernate |
| Frontend   | Angular 19, TypeScript, WebSocket                     |
| Payments   | Stripe Integration                                    |
| Deployment | Docker and Docker Compose                             |

---

## Getting Started

### Prerequisites

* Docker and Docker Compose
* Git
* Java 21

### Quick Start

1. Clone the repository

```bash
git clone https://github.com/your-repo-url.git
cd egypt-smart-journey-planner
```

2. Start the chatbot services

```bash
docker-compose up rasa
```

3. Run the backend (Spring Boot Application)

```bash
./mvnw spring-boot:run
```

4. Start the frontend

```bash
cd frontend
npm install
npm start
```

### Service Ports

| Service            | Port             |
| ------------------ | ---------------- |
| Rasa Core          | 5005             |
| Rasa Action Server | 5055             |
| API Services       | 8000, 8001, 8002 |
| Angular Frontend   | 4200             |

---

## Use Cases

* Individual Travelers – Get personalized recommendations via AI chat
* Travel Agencies – Manage trip offerings and bookings
* Smart Planning – AI-powered itinerary optimization

---

## UI Preview

Here are some snapshots of the platform:


---

## Team


---

## Notes

This project is a complete travel technology solution for the Egyptian tourism industry.
It combines modern web development practices with AI-powered recommendations to create a personalized and intuitive travel planning experience.

The modular architecture ensures easy scalability and maintenance, making it suitable for future enhancements.
