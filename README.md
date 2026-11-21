# Planora

Planora is a full-stack travel planner that generates itineraries, shows weather forecasts, suggests nearby hotels and restaurants, visualizes places on a map, tracks budgets, stores recent trips in the browser, and supports light/dark mode.

It uses a Flask backend for API integrations and trip planning, and a vanilla HTML/CSS/JavaScript frontend for the user experience.

## Overview

Planora helps a user:

- choose a destination
- select start and end dates
- enter a budget
- generate a multi-day itinerary
- view weather and destination information
- explore attractions, hotels, and restaurants on a map
- save recent trips in the browser

## Main Features

- Day-by-day itinerary generation
- Live weather forecasting (Open-Meteo)
- Destination autocomplete
- Attraction discovery (OpenTripMap & OpenStreetMap)
- Hotel and restaurant suggestions
- Budget breakdown and local currency conversion (Frankfurter)
- Destination intel panel (capitals, regions, currencies)
- **Popular Destination Chips** (instant 1-click trip loading)
- **Interactive Map Layer Filters** (Attractions, Hotels, Restaurants)
- **Smart Weather-Aware Packing Checklist** (dynamic rain/sun/cold checklist)
- **Export & Print PDF Itinerary**
- **Share / Copy Trip Summary**
- Browser-based login and recent trips
- High-contrast persistent Dark Mode & Light Mode

## Tech Stack

### Frontend

- HTML5
- CSS3
- Vanilla JavaScript
- Leaflet.js

### Backend

- Python
- Flask
- Flask-CORS
- Requests
- python-dotenv

## Project Structure

```text
Planora/
|-- app.py
|-- app-enhanced.js
|-- index.html
|-- style.css
|-- REQUIREMENTS.txt
|-- script.js
`-- README.md
```

## File Guide

### `app.py`

Main Flask backend.

Responsibilities:

- geocoding destinations
- destination autocomplete
- fetching weather
- fetching attractions
- building itineraries
- route summaries
- country metadata
- budget currency conversion
- hotel and restaurant suggestions

### `app-enhanced.js`

Active frontend script loaded by `index.html`.

Responsibilities:

- form submission
- login/signup modal flow
- recent trip storage
- dark mode toggle
- weather rendering
- itinerary rendering
- budget rendering
- destination suggestions dropdown
- map initialization
- marker rendering for attractions, hotels, and restaurants

### `index.html`

Main page layout.

Contains:

- navbar
- hero section
- planner form
- weather container
- destination intel section
- itinerary section
- budget section
- suggestions section
- map section
- recent trips section
- auth modal

### `style.css`

Application styling.

Includes:

- base layout
- product-style refresh
- animations and hover states
- modal styling
- map and card styling
- dark mode overrides

### `REQUIREMENTS.txt`

Python dependencies:

- `flask==3.0.3`
- `flask-cors==4.0.1`
- `requests==2.32.3`
- `python-dotenv==1.0.1`

### `script.js`

Older frontend script still present in the repository. The live page currently uses `app-enhanced.js`.

## How The App Works

### Step 1. User fills the trip form

The user enters:

- destination
- start date
- end date
- budget

### Step 2. Frontend requests the trip plan

The frontend sends a `POST` request to:

- `/plan-trip`

This returns the main trip data:

- weather
- itinerary
- budget breakdown
- attraction markers
- destination metadata
- country insights
- currency conversion
- coordinates

### Step 3. Frontend requests nearby suggestions

After the main plan is rendered, the frontend sends a second request to:

- `/suggestions`

This returns:

- hotels
- restaurants

These are rendered as cards and also added to the map.

### Step 4. Optional local trip saving

If the user is logged in, the trip is stored in browser `localStorage` and shown in the Recent Trips section.

## Backend Endpoints

### `GET /search-destinations`

Used for destination autocomplete.

Query parameter:

- `q`

Example:

```http
GET /search-destinations?q=paris
```

Returns destination suggestions with fields such as:

- `display_name`
- `lat`
- `lon`
- `country`
- `country_code`
- `state`
- `city`

### `POST /plan-trip`

Generates the main trip plan.

Example request:

```json
{
  "destination": "Japan",
  "startDate": "2026-04-08",
  "endDate": "2026-04-20",
  "budget": 500000,
  "numDays": 13
}
```

Main response fields:

- `weather`
- `itinerary`
- `budgetBreakdown`
- `attractions`
- `currency`
- `destinationMeta`
- `countryInsights`
- `coordinates`

### `POST /suggestions`

Returns nearby hotels and restaurants for the selected destination.

Example request:

```json
{
  "destination": "Japan",
  "budget": 500000
}
```

Main response fields:

- `hotels`
- `restaurants`

## External APIs Used

### Open-Meteo

Used for:

- trip weather forecasts

Website:

- [https://open-meteo.com](https://open-meteo.com)

### OpenTripMap

Used for:

- tourist attractions

Website:

- [https://opentripmap.com](https://opentripmap.com)

Environment variable:

- `OPENTRIPMAP_KEY`

If this key is missing, the app falls back to OSM attraction data.

### Nominatim

Used for:

- geocoding
- destination search suggestions

Website:

- [https://nominatim.openstreetmap.org](https://nominatim.openstreetmap.org)

### Overpass API

Used for:

- nearby hotels
- nearby restaurants
- attraction fallback

Website:

- [https://overpass-api.de](https://overpass-api.de)

### Rest Countries

Used for:

- country metadata
- region
- capital
- currency details

Website:

- [https://restcountries.com](https://restcountries.com)

### Frankfurter

Used for:

- currency conversion

Website:

- [https://www.frankfurter.app](https://www.frankfurter.app)

### OSRM

Used for:

- route summaries for itinerary places

Website:

- [https://project-osrm.org](https://project-osrm.org)

### Ticketmaster

Backend support still exists for event data through:

- `TICKETMASTER_KEY`

But event rendering is not currently part of the active frontend experience.

## Setup Instructions

### 1. Open the project directory

```powershell
cd "C:\Users\varun\OneDrive\Desktop\Planora"
```

### 2. Create a virtual environment

```powershell
py -m venv .venv
```

### 3. Activate the virtual environment

```powershell
.venv\Scripts\Activate.ps1
```

### 4. Install Python dependencies

```powershell
py -m pip install -r REQUIREMENTS.txt
```

### 5. Create a `.env` file

Example:

```env
OPENTRIPMAP_KEY=your_opentripmap_key_here
TICKETMASTER_KEY=your_ticketmaster_key_here
```

Notes:

- `OPENTRIPMAP_KEY` is the most important optional key for visible attraction quality
- `TICKETMASTER_KEY` is currently not required for the active UI

### 6. Start the App

```powershell
python app.py
```

Open your browser and navigate to:

- [http://localhost:5000](http://localhost:5000)

The Flask app now serves both the frontend web interface and all backend APIs in one single command. (Optional: running a separate static file server on port 5500 is also supported).

## Cloud Deployment (Render.com / Railway / Fly.io)

Planora is 100% production-ready for free cloud deployment:

### Deploying to Render.com (Recommended Free Host)
1. Push your repository to **GitHub**.
2. Sign in to [Render.com](https://render.com) and click **New + → Web Service**.
3. Connect your GitHub repository.
4. Set the following settings:
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r REQUIREMENTS.txt`
   - **Start Command:** `gunicorn app:app`
5. *(Optional)* Under **Environment Variables**, add:
   - `OPENTRIPMAP_KEY = your_key_if_you_have_one`
6. Click **Deploy Web Service**. You will receive a live `https://planora.onrender.com` URL!

## Local Storage Model

The frontend stores data in the browser using these keys:

- `planora.users`
- `planora.session`
- `planora.trips`
- `planora.theme`

### What each key stores

- `planora.users`
  Local demo accounts

- `planora.session`
  Current logged-in user session

- `planora.trips`
  Saved recent trips for logged-in users

- `planora.theme`
  Light or dark mode preference

## Important Behaviors

### English-first text handling

The app tries to keep visible text in English by:

- requesting English destination results from Nominatim
- preferring English place tags from OpenStreetMap where possible
- falling back to generic English labels when English names are not available

### Weather reliability improvements

The backend:

- uses a dedicated HTTP session
- ignores broken proxy environment settings
- clamps weather requests to the available Open-Meteo forecast window

This prevents long trips from failing the entire weather section.

### Attraction fallback strategy

The app first tries OpenTripMap. If it is not configured or returns nothing useful, the backend falls back to attraction data from OpenStreetMap through Overpass.

### Suggestions loading strategy

Hotels and restaurants load after the core itinerary. This makes the primary trip plan appear first instead of blocking the UI on slower Overpass responses.

## Current UI Areas

- Navbar
- Hero section
- Account banner
- Trip form
- Destination suggestions dropdown
- Weather card
- Destination intel cards
- Itinerary timeline
- Budget card
- Hotel and restaurant suggestion cards
- Interactive map
- Recent trips grid
- Authentication modal

## Known Limitations

- Login and signup are local-only and not secure for production use
- Recent trips are stored only in the current browser
- Overpass can sometimes return slow, inconsistent, or empty results
- Attraction quality depends on the destination and available third-party data
- `script.js` is still present even though `app-enhanced.js` is the active script
- Ticketmaster support remains in the backend but is not active in the frontend

## Troubleshooting

### Weather not showing

Check:

- Flask backend is running
- the backend was restarted after code changes
- you refreshed the browser with `Ctrl + F5`

Restart backend:

```powershell
cd "C:\Users\varun\OneDrive\Desktop\Planora"
py app.py
```

### Hotels or restaurants missing

Possible reasons:

- Overpass returned no nearby data
- the chosen destination is too broad
- the external service is temporarily slow or empty

Try a more specific city or district name.

### Destination suggestions not appearing

Make sure:

- the backend is running on `http://localhost:5000`
- the frontend is loaded from `http://localhost:5500/index.html`

### Dark mode or style changes not appearing

Use a hard refresh:

- `Ctrl + F5`

## Improvement Ideas

- replace local storage auth with real backend authentication
- store trips in a database
- remove or archive `script.js`
- add backend tests for route behavior and date edge cases
- add keyboard navigation for destination suggestions
- add map filtering by marker type
- improve retries and fallback messaging for external API failures

## Credits

Built with:

- Flask
- Leaflet
- Open-Meteo
- OpenTripMap
- OpenStreetMap
- Overpass API
- Rest Countries
- Frankfurter
- OSRM

## License

Add a license if you plan to publish or distribute the project.
