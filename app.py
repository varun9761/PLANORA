"""
============================================================
  PLANORA — Flask Backend & Web Application
============================================================

  APIs used:
    • Open-Meteo        → live weather (no key, completely free)
    • OpenTripMap       → tourist attractions (free key optional)
    • Nominatim (OSM)   → geocoding & attraction / POI discovery (no key)
    • Frankfurter       → real-time currency conversion (no key)
    • OSRM              → route driving summaries (no key)

  Setup & Run:
    1. pip install -r REQUIREMENTS.txt
    2. python app.py
    3. Visit http://localhost:5000 in your browser!
============================================================
"""

import os
import sys
import json
import math
import requests

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)

HTTP = requests.Session()
HTTP.trust_env = False

DEFAULT_HEADERS = {
    "User-Agent": "Planora/2.0 (travel-planner-app)",
    "Accept-Language": "en",
}

# ── Optional API keys from .env file ──────────────────────────
OPENTRIPMAP_KEY = os.environ.get("OPENTRIPMAP_KEY", "").strip()
TICKETMASTER_KEY = os.environ.get("TICKETMASTER_KEY", "").strip()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()

# ── WMO weather codes → human readable ─────────────────────────
WMO = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Icy fog",
    51: "Light drizzle",
    53: "Drizzle",
    55: "Heavy drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    80: "Showers",
    81: "Heavy showers",
    82: "Violent showers",
    95: "Thunderstorm",
    99: "Hailstorm",
}

DAY_THEMES = [
    "Arrival & City Highlights",
    "History & Culture",
    "Nature & Adventure",
    "Local Life & Hidden Gems",
    "Leisure & Exploration",
    "Shopping & Farewell",
]

FALLBACK_ACTIVITIES = [
    [
        "Settle in and take an easy walk around the city center",
        "Visit a popular local market or main square",
    ],
    [
        "Explore a museum, monument, or historic district",
        "Take a guided heritage walk or self-guided culture trail",
    ],
    [
        "Spend time at a scenic park, waterfront, or viewpoint",
        "Try an outdoor activity or short nature excursion",
    ],
    [
        "Explore neighborhood cafes and local food spots",
        "Browse artisan streets, local shops, or community markets",
    ],
    [
        "Keep the day flexible for spontaneous discoveries",
        "Relax at a garden, promenade, or scenic hangout",
    ],
    [
        "Pick up souvenirs and revisit a favorite area",
        "Enjoy a relaxed final meal before departure",
    ],
]

# ── Comprehensive Country Intelligence Database ────────────────
COUNTRY_DATA = {
    "IN": {"country": "India", "capital": "New Delhi", "region": "Asia", "subregion": "Southern Asia", "currencyCode": "INR", "currencyName": "Indian Rupee", "currencySymbol": "₹", "flag": "🇮🇳"},
    "US": {"country": "United States", "capital": "Washington, D.C.", "region": "Americas", "subregion": "North America", "currencyCode": "USD", "currencyName": "US Dollar", "currencySymbol": "$", "flag": "🇺🇸"},
    "GB": {"country": "United Kingdom", "capital": "London", "region": "Europe", "subregion": "Northern Europe", "currencyCode": "GBP", "currencyName": "British Pound", "currencySymbol": "£", "flag": "🇬🇧"},
    "FR": {"country": "France", "capital": "Paris", "region": "Europe", "subregion": "Western Europe", "currencyCode": "EUR", "currencyName": "Euro", "currencySymbol": "€", "flag": "🇫🇷"},
    "IT": {"country": "Italy", "capital": "Rome", "region": "Europe", "subregion": "Southern Europe", "currencyCode": "EUR", "currencyName": "Euro", "currencySymbol": "€", "flag": "🇮🇹"},
    "ES": {"country": "Spain", "capital": "Madrid", "region": "Europe", "subregion": "Southern Europe", "currencyCode": "EUR", "currencyName": "Euro", "currencySymbol": "€", "flag": "🇪🇸"},
    "DE": {"country": "Germany", "capital": "Berlin", "region": "Europe", "subregion": "Western Europe", "currencyCode": "EUR", "currencyName": "Euro", "currencySymbol": "€", "flag": "🇩🇪"},
    "JP": {"country": "Japan", "capital": "Tokyo", "region": "Asia", "subregion": "Eastern Asia", "currencyCode": "JPY", "currencyName": "Japanese Yen", "currencySymbol": "¥", "flag": "🇯🇵"},
    "AE": {"country": "United Arab Emirates", "capital": "Abu Dhabi", "region": "Middle East", "subregion": "Western Asia", "currencyCode": "AED", "currencyName": "UAE Dirham", "currencySymbol": "د.إ", "flag": "🇦🇪"},
    "TH": {"country": "Thailand", "capital": "Bangkok", "region": "Asia", "subregion": "South-Eastern Asia", "currencyCode": "THB", "currencyName": "Thai Baht", "currencySymbol": "฿", "flag": "🇹🇭"},
    "SG": {"country": "Singapore", "capital": "Singapore", "region": "Asia", "subregion": "South-Eastern Asia", "currencyCode": "SGD", "currencyName": "Singapore Dollar", "currencySymbol": "S$", "flag": "🇸🇬"},
    "AU": {"country": "Australia", "capital": "Canberra", "region": "Oceania", "subregion": "Australia and New Zealand", "currencyCode": "AUD", "currencyName": "Australian Dollar", "currencySymbol": "A$", "flag": "🇦🇺"},
    "CA": {"country": "Canada", "capital": "Ottawa", "region": "Americas", "subregion": "North America", "currencyCode": "CAD", "currencyName": "Canadian Dollar", "currencySymbol": "C$", "flag": "🇨🇦"},
    "CH": {"country": "Switzerland", "capital": "Bern", "region": "Europe", "subregion": "Western Europe", "currencyCode": "CHF", "currencyName": "Swiss Franc", "currencySymbol": "CHF", "flag": "🇨🇭"},
    "ID": {"country": "Indonesia", "capital": "Jakarta", "region": "Asia", "subregion": "South-Eastern Asia", "currencyCode": "IDR", "currencyName": "Indonesian Rupiah", "currencySymbol": "Rp", "flag": "🇮🇩"},
    "VN": {"country": "Vietnam", "capital": "Hanoi", "region": "Asia", "subregion": "South-Eastern Asia", "currencyCode": "VND", "currencyName": "Vietnamese Dong", "currencySymbol": "₫", "flag": "🇻🇳"},
    "MY": {"country": "Malaysia", "capital": "Kuala Lumpur", "region": "Asia", "subregion": "South-Eastern Asia", "currencyCode": "MYR", "currencyName": "Malaysian Ringgit", "currencySymbol": "RM", "flag": "🇲🇾"},
    "MV": {"country": "Maldives", "capital": "Malé", "region": "Asia", "subregion": "Southern Asia", "currencyCode": "MVR", "currencyName": "Maldivian Rufiyaa", "currencySymbol": "Rf", "flag": "🇲🇻"},
    "TR": {"country": "Turkey", "capital": "Ankara", "region": "Europe / Asia", "subregion": "Western Asia", "currencyCode": "TRY", "currencyName": "Turkish Lira", "currencySymbol": "₺", "flag": "🇹🇷"},
    "GR": {"country": "Greece", "capital": "Athens", "region": "Europe", "subregion": "Southern Europe", "currencyCode": "EUR", "currencyName": "Euro", "currencySymbol": "€", "flag": "🇬🇷"},
    "PT": {"country": "Portugal", "capital": "Lisbon", "region": "Europe", "subregion": "Southern Europe", "currencyCode": "EUR", "currencyName": "Euro", "currencySymbol": "€", "flag": "🇵🇹"},
    "NL": {"country": "Netherlands", "capital": "Amsterdam", "region": "Europe", "subregion": "Western Europe", "currencyCode": "EUR", "currencyName": "Euro", "currencySymbol": "€", "flag": "🇳🇱"},
    "EG": {"country": "Egypt", "capital": "Cairo", "region": "Africa", "subregion": "Northern Africa", "currencyCode": "EGP", "currencyName": "Egyptian Pound", "currencySymbol": "E£", "flag": "🇪🇬"},
    "ZA": {"country": "South Africa", "capital": "Pretoria / Cape Town", "region": "Africa", "subregion": "Southern Africa", "currencyCode": "ZAR", "currencyName": "South African Rand", "currencySymbol": "R", "flag": "🇿🇦"},
    "BR": {"country": "Brazil", "capital": "Brasília", "region": "Americas", "subregion": "South America", "currencyCode": "BRL", "currencyName": "Brazilian Real", "currencySymbol": "R$", "flag": "🇧🇷"},
    "MX": {"country": "Mexico", "capital": "Mexico City", "region": "Americas", "subregion": "North America", "currencyCode": "MXN", "currencyName": "Mexican Peso", "currencySymbol": "Mex$", "flag": "🇲🇽"},
    "NZ": {"country": "New Zealand", "capital": "Wellington", "region": "Oceania", "subregion": "Australia and New Zealand", "currencyCode": "NZD", "currencyName": "New Zealand Dollar", "currencySymbol": "NZ$", "flag": "🇳🇿"},
    "NP": {"country": "Nepal", "capital": "Kathmandu", "region": "Asia", "subregion": "Southern Asia", "currencyCode": "NPR", "currencyName": "Nepalese Rupee", "currencySymbol": "₨", "flag": "🇳🇵"},
    "LK": {"country": "Sri Lanka", "capital": "Colombo", "region": "Asia", "subregion": "Southern Asia", "currencyCode": "LKR", "currencyName": "Sri Lankan Rupee", "currencySymbol": "Rs", "flag": "🇱🇰"},
    "KR": {"country": "South Korea", "capital": "Seoul", "region": "Asia", "subregion": "Eastern Asia", "currencyCode": "KRW", "currencyName": "South Korean Won", "currencySymbol": "₩", "flag": "🇰🇷"},
    "CN": {"country": "China", "capital": "Beijing", "region": "Asia", "subregion": "Eastern Asia", "currencyCode": "CNY", "currencyName": "Chinese Yuan", "currencySymbol": "¥", "flag": "🇨🇳"},
    "RU": {"country": "Russia", "capital": "Moscow", "region": "Europe / Asia", "subregion": "Eastern Europe", "currencyCode": "RUB", "currencyName": "Russian Ruble", "currencySymbol": "₽", "flag": "🇷🇺"},
    "SE": {"country": "Sweden", "capital": "Stockholm", "region": "Europe", "subregion": "Northern Europe", "currencyCode": "SEK", "currencyName": "Swedish Krona", "currencySymbol": "kr", "flag": "🇸🇪"},
    "NO": {"country": "Norway", "capital": "Oslo", "region": "Europe", "subregion": "Northern Europe", "currencyCode": "NOK", "currencyName": "Norwegian Krone", "currencySymbol": "kr", "flag": "🇳🇴"},
    "DK": {"country": "Denmark", "capital": "Copenhagen", "region": "Europe", "subregion": "Northern Europe", "currencyCode": "DKK", "currencyName": "Danish Krone", "currencySymbol": "kr", "flag": "🇩🇰"},
    "AT": {"country": "Austria", "capital": "Vienna", "region": "Europe", "subregion": "Western Europe", "currencyCode": "EUR", "currencyName": "Euro", "currencySymbol": "€", "flag": "🇦🇹"},
    "BE": {"country": "Belgium", "capital": "Brussels", "region": "Europe", "subregion": "Western Europe", "currencyCode": "EUR", "currencyName": "Euro", "currencySymbol": "€", "flag": "🇧🇪"},
    "IE": {"country": "Ireland", "capital": "Dublin", "region": "Europe", "subregion": "Northern Europe", "currencyCode": "EUR", "currencyName": "Euro", "currencySymbol": "€", "flag": "🇮🇪"},
    "CZ": {"country": "Czech Republic", "capital": "Prague", "region": "Europe", "subregion": "Central Europe", "currencyCode": "CZK", "currencyName": "Czech Koruna", "currencySymbol": "Kč", "flag": "🇨🇿"},
    "HU": {"country": "Hungary", "capital": "Budapest", "region": "Europe", "subregion": "Central Europe", "currencyCode": "HUF", "currencyName": "Hungarian Forint", "currencySymbol": "Ft", "flag": "🇭🇺"},
    "PL": {"country": "Poland", "capital": "Warsaw", "region": "Europe", "subregion": "Central Europe", "currencyCode": "PLN", "currencyName": "Polish Zloty", "currencySymbol": "zł", "flag": "🇵🇱"},
    "SA": {"country": "Saudi Arabia", "capital": "Riyadh", "region": "Middle East", "subregion": "Western Asia", "currencyCode": "SAR", "currencyName": "Saudi Riyal", "currencySymbol": "﷼", "flag": "🇸🇦"},
    "QA": {"country": "Qatar", "capital": "Doha", "region": "Middle East", "subregion": "Western Asia", "currencyCode": "QAR", "currencyName": "Qatari Riyal", "currencySymbol": "﷼", "flag": "🇶🇦"},
    "OM": {"country": "Oman", "capital": "Muscat", "region": "Middle East", "subregion": "Western Asia", "currencyCode": "OMR", "currencyName": "Omani Rial", "currencySymbol": "﷼", "flag": "🇴🇲"},
    "PH": {"country": "Philippines", "capital": "Manila", "region": "Asia", "subregion": "South-Eastern Asia", "currencyCode": "PHP", "currencyName": "Philippine Peso", "currencySymbol": "₱", "flag": "🇵🇭"},
    "MA": {"country": "Morocco", "capital": "Rabat", "region": "Africa", "subregion": "Northern Africa", "currencyCode": "MAD", "currencyName": "Moroccan Dirham", "currencySymbol": "د.م.", "flag": "🇲🇦"},
    "KE": {"country": "Kenya", "capital": "Nairobi", "region": "Africa", "subregion": "Eastern Africa", "currencyCode": "KES", "currencyName": "Kenyan Shilling", "currencySymbol": "KSh", "flag": "🇰🇪"},
    "PE": {"country": "Peru", "capital": "Lima", "region": "Americas", "subregion": "South America", "currencyCode": "PEN", "currencyName": "Peruvian Sol", "currencySymbol": "S/", "flag": "🇵🇪"},
    "AR": {"country": "Argentina", "capital": "Buenos Aires", "region": "Americas", "subregion": "South America", "currencyCode": "ARS", "currencyName": "Argentine Peso", "currencySymbol": "$", "flag": "🇦🇷"},
    "HR": {"country": "Croatia", "capital": "Zagreb", "region": "Europe", "subregion": "Southern Europe", "currencyCode": "EUR", "currencyName": "Euro", "currencySymbol": "€", "flag": "🇭🇷"},
    "IS": {"country": "Iceland", "capital": "Reykjavik", "region": "Europe", "subregion": "Northern Europe", "currencyCode": "ISK", "currencyName": "Icelandic Krona", "currencySymbol": "kr", "flag": "🇮🇸"},
    "FI": {"country": "Finland", "capital": "Helsinki", "region": "Europe", "subregion": "Northern Europe", "currencyCode": "EUR", "currencyName": "Euro", "currencySymbol": "€", "flag": "🇫🇮"},
}

# Secondary index by country name lowercase
COUNTRY_NAME_INDEX = {v["country"].lower(): v for v in COUNTRY_DATA.values()}

# Benchmark INR conversion fallback rates
FALLBACK_INR_RATES = {
    "USD": 0.012, "EUR": 0.011, "GBP": 0.0095, "AED": 0.044, "THB": 0.42,
    "SGD": 0.016, "JPY": 1.85, "AUD": 0.018, "CAD": 0.016, "CHF": 0.011,
    "IDR": 185.0, "VND": 300.0, "MYR": 0.056, "TRY": 0.41, "BRL": 0.068,
    "MXN": 0.24, "NZD": 0.020, "KRW": 16.5, "CNY": 0.086, "RUB": 1.15,
    "SEK": 0.13, "NOK": 0.13, "DKK": 0.082, "CZK": 0.28, "HUF": 4.4,
    "ZAR": 0.22, "EGP": 0.58, "LKR": 3.6, "NPR": 1.6, "SAR": 0.045,
    "QAR": 0.044, "OMR": 0.0046, "PHP": 0.68, "MAD": 0.12, "KES": 1.55,
}

# ── Destination Cost-of-Living Tier Matrix (Tier 1 = High Cost, Tier 4 = High Value) ──
COUNTRY_COST_TIERS = {
    "CH": 1, "US": 1, "GB": 1, "FR": 1, "DE": 1, "NL": 1, "AT": 1, "BE": 1,
    "IE": 1, "SE": 1, "NO": 1, "DK": 1, "IS": 1, "FI": 1, "AU": 1, "NZ": 1,
    "CA": 1, "JP": 1, "SG": 1,
    "IT": 2, "ES": 2, "PT": 2, "GR": 2, "HR": 2, "AE": 2, "QA": 2, "SA": 2,
    "OM": 2, "KR": 2, "CZ": 2, "HU": 2, "PL": 2,
    "TH": 3, "ID": 3, "VN": 3, "MY": 3, "MV": 3, "TR": 3, "EG": 3, "ZA": 3,
    "BR": 3, "MX": 3, "PE": 3, "AR": 3, "MA": 3, "KE": 3, "PH": 3, "CN": 3, "RU": 3,
    "IN": 4, "NP": 4, "LK": 4,
}

COST_TIER_PROFILES = {
    1: {
        "label": "Tier 1 • Premium Global Destination",
        "min_daily": 8500,
        "comfort_daily": 16000,
        "luxury_daily": 30000,
        "weights": {"accommodation": 0.46, "food": 0.22, "transport": 0.14, "activities": 0.12, "misc": 0.06},
    },
    2: {
        "label": "Tier 2 • Moderate International",
        "min_daily": 5000,
        "comfort_daily": 9500,
        "luxury_daily": 18500,
        "weights": {"accommodation": 0.42, "food": 0.23, "transport": 0.14, "activities": 0.14, "misc": 0.07},
    },
    3: {
        "label": "Tier 3 • Value International",
        "min_daily": 2500,
        "comfort_daily": 5500,
        "luxury_daily": 11000,
        "weights": {"accommodation": 0.36, "food": 0.25, "transport": 0.14, "activities": 0.17, "misc": 0.08},
    },
    4: {
        "label": "Tier 4 • High-Value Domestic / South Asia",
        "min_daily": 1500,
        "comfort_daily": 3500,
        "luxury_daily": 7500,
        "weights": {"accommodation": 0.35, "food": 0.26, "transport": 0.15, "activities": 0.16, "misc": 0.08},
    },
}

STYLE_MULTIPLIERS = {
    "solo": 0.90,
    "couple": 1.25,
    "family": 1.45,
    "friends": 0.85,
}

TRAVEL_STYLE_NOTES = {
    "solo": "Flexible solo pace — prioritize walkable clusters, social cafes, and central transit hubs.",
    "couple": "Romantic & scenic vibe — includes sunset viewpoints, boutique dining alleys, and relaxed pacing.",
    "family": "Family-friendly routing — minimal transit hops, engaging cultural stops, and comfortable mid-day breaks.",
    "friends": "Group adventure mode — energetic sightseeing, lively night markets, and shared dining hotspots.",
}

DEST_CUISINE_TIPS = {
    "amritsar": [
        "Morning: Crispy Amritsari Aloo Kulcha with chilled Sweet Lassi near Hall Bazaar.",
        "Lunch: Iconic Langar community meal at Golden Temple or Dal Makhani at Kesar Da Dhaba.",
        "Evening: Street-side Tandoori Paneer Tikka & Jalebi in Lawrence Road food lane.",
    ],
    "jaipur": [
        "Morning: Pyaaz Kachori & Masala Chai at Rawat Mishtan Bhandar.",
        "Lunch: Authentic Rajasthani Dal Baati Churma thali in Johari Bazaar.",
        "Evening: Rooftop dining overlooking illuminated forts with Laal Maas or Gatte ki Sabzi.",
    ],
    "delhi": [
        "Morning: Bedmi Puri & Halwa in Old Delhi's Chandni Chowk lanes.",
        "Lunch: Chole Bhature in Paharganj or Paranthas at Paranthe Wali Gali.",
        "Evening: Kebabs around Jama Masjid or gourmet fusion cafes in Khan Market.",
    ],
    "goa": [
        "Morning: Poee bread omelette & filter coffee at a sunny beach shack.",
        "Lunch: Authentic Goan Fish Curry Rice or Chicken Xacuti by the coast.",
        "Evening: Fresh grilled seafood & Bebinca dessert overlooking the Arabian Sea.",
    ],
    "paris": [
        "Morning: Warm butter croissant & espresso at a neighborhood boulangerie.",
        "Lunch: Bistro Steak Frites or savory buckwheat galette in Le Marais.",
        "Evening: Artisanal macarons, French onion soup, and Seine-side cafe culture.",
    ],
    "tokyo": [
        "Morning: Fresh nigiri sushi & matcha desserts near Tsukiji Outer Market.",
        "Lunch: Rich Tonkotsu Ramen or crispy Tonkatsu in Shinjuku.",
        "Evening: Izakaya yakitori skewers and takoyaki in atmospheric lantern alleys.",
    ],
    "rome": [
        "Morning: Cornetto pastry & cappuccino standing at a classic espresso bar.",
        "Lunch: Roman-style Cacio e Pepe or Carbonara near Campo de' Fiori.",
        "Evening: Thin-crust Pizza al Taglio and artisan pistachio gelato in Trastevere.",
    ],
    "new york": [
        "Morning: Classic New York bagel with lox & cream cheese in Manhattan.",
        "Lunch: Iconic dollar-slice or wood-fired pizza & pastrami deli sandwich.",
        "Evening: Diverse street eats in Chelsea Market or rooftop dining in SoHo.",
    ],
    "dubai": [
        "Morning: Arabic Shakshuka, Karak Chai & fresh flatbreads in Al Fahidi.",
        "Lunch: Authentic Emirati Machboos or Levantine mezze platters.",
        "Evening: Waterfront dining by Dubai Fountain or spiced street shawarma in Deira.",
    ],
    "bali": [
        "Morning: Tropical smoothie bowls & Balinese Kopi Tubruk coffee in Ubud.",
        "Lunch: Nasi Campur platter or Crispy Duck (Bebek Betutu) overlooking rice fields.",
        "Evening: Fresh Jimbaran Bay grilled seafood on the beach at sunset.",
    ],
}


def evaluate_budget_intelligence(budget: int, num_days: int, country_code: str, travel_style: str = "solo") -> dict:
    """Compute realistic destination cost-of-living feasibility and dynamic allocation."""
    tier_id = COUNTRY_COST_TIERS.get((country_code or "").upper(), 3)
    profile = COST_TIER_PROFILES[tier_id]
    mult = STYLE_MULTIPLIERS.get(travel_style, 1.0)

    min_daily = round(profile["min_daily"] * mult)
    comfort_daily = round(profile["comfort_daily"] * mult)
    luxury_daily = round(profile["luxury_daily"] * mult)

    days = max(1, num_days)
    daily_budget = round(budget / days) if budget > 0 else 0

    weights = profile["weights"]
    breakdown = {
        k: round(budget * w)
        for k, w in weights.items()
    }

    if budget <= 0:
        status = "unassigned"
        status_label = "No Budget Set"
        badge_color = "#64748b"
        advice = f"Estimated comfortable budget for {days} days ({travel_style}): ~₹{(comfort_daily * days):,}."
    elif daily_budget >= luxury_daily:
        status = "luxury"
        status_label = "Luxury & Premium"
        badge_color = "#8b5cf6"
        advice = f"Generous ₹{daily_budget:,}/day allows 5-star stays, private transfers, and fine dining."
    elif daily_budget >= comfort_daily:
        status = "comfortable"
        status_label = "Comfortable Budget"
        badge_color = "#10b981"
        advice = f"Well-balanced ₹{daily_budget:,}/day covers boutique stays, guided tours, and great dining."
    elif daily_budget >= min_daily:
        status = "tight"
        status_label = "Smart Backpacker / Tight"
        badge_color = "#f59e0b"
        advice = f"₹{daily_budget:,}/day is tight for this destination. Prioritize hostels, public transit & street food."
    else:
        status = "underfunded"
        status_label = "Below Recommended"
        badge_color = "#ef4444"
        advice = f"₹{daily_budget:,}/day is below the ₹{min_daily:,}/day baseline. Consider shortening trip or raising budget to ₹{(min_daily * days):,}."

    return {
        "breakdown": breakdown,
        "intelligence": {
            "tier": tier_id,
            "tierLabel": profile["label"],
            "status": status,
            "statusLabel": status_label,
            "badgeColor": badge_color,
            "dailyBudget": daily_budget,
            "recommendedDaily": comfort_daily,
            "minDaily": min_daily,
            "recommendedTotal": comfort_daily * days,
            "advice": advice,
        },
    }


def api_get(url: str, **kwargs):
    headers = {**DEFAULT_HEADERS, **kwargs.pop("headers", {})}
    return HTTP.get(url, headers=headers, **kwargs)


def api_post(url: str, **kwargs):
    headers = {**DEFAULT_HEADERS, **kwargs.pop("headers", {})}
    return HTTP.post(url, headers=headers, **kwargs)


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two coordinates in kilometers."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 1)


# ════════════════════════════════════════════════════════════════
# CORE SERVICES
# ════════════════════════════════════════════════════════════════

def search_destinations(query: str, limit: int = 5) -> list:
    """Return destination suggestions with lat/lon and country details."""
    try:
        r = api_get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": query,
                "format": "jsonv2",
                "limit": limit,
                "addressdetails": 1,
                "accept-language": "en",
            },
            timeout=8,
        )
        r.raise_for_status()
        suggestions = []
        for item in r.json():
            address = item.get("address", {})
            country_name = address.get("country", "")
            country_code = (address.get("country_code") or "").upper()
            display_name = item.get("display_name") or query.title()

            city = (
                address.get("city")
                or address.get("town")
                or address.get("village")
                or address.get("county")
                or ""
            )
            state = address.get("state") or address.get("region") or ""

            suggestions.append({
                "display_name": display_name,
                "lat": float(item["lat"]),
                "lon": float(item["lon"]),
                "country": country_name,
                "country_code": country_code,
                "state": state,
                "city": city,
            })
        return suggestions
    except Exception as e:
        print(f"[search_destinations] {e}")
        return []


def fetch_weather(lat: float, lon: float, start_date: str, num_days: int) -> dict:
    """Fetch live weather from Open-Meteo with comprehensive date bounds checking."""
    try:
        trip_start = datetime.strptime(start_date, "%Y-%m-%d").date()
        trip_end = trip_start + timedelta(days=num_days - 1)
        today = datetime.now().date()
        max_forecast_end = today + timedelta(days=15)

        if trip_end < today:
            return {"temp": "N/A", "condition": "Past travel dates", "_daily": []}

        if trip_start > max_forecast_end:
            return {"temp": "N/A", "condition": "Forecast unavailable (date too far ahead)", "_daily": []}

        request_start = max(trip_start, today)
        request_end = min(trip_end, max_forecast_end)

        if request_start > request_end:
            return {"temp": "N/A", "condition": "Forecast unavailable", "_daily": []}

        r = api_get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "daily": "temperature_2m_max,temperature_2m_min,weather_code",
                "timezone": "auto",
                "start_date": request_start.strftime("%Y-%m-%d"),
                "end_date": request_end.strftime("%Y-%m-%d"),
            },
            timeout=8,
        )
        r.raise_for_status()
        d = r.json().get("daily", {})
        t_max = d.get("temperature_2m_max", [])
        t_min = d.get("temperature_2m_min", [])
        codes = d.get("weather_code", d.get("weathercode", []))
        dates = d.get("time", [])

        temp = round((t_max[0] + t_min[0]) / 2) if t_max and t_min else "N/A"
        condition = WMO.get(int(codes[0]), "Variable weather") if codes else "Variable weather"

        daily = []
        for i in range(min(num_days, len(t_max))):
            daily.append({
                "date": dates[i] if i < len(dates) else "",
                "temp_max": t_max[i] if i < len(t_max) else None,
                "temp_min": t_min[i] if i < len(t_min) else None,
                "condition": WMO.get(int(codes[i]), "Variable") if i < len(codes) else "Variable",
            })

        return {"temp": temp, "condition": condition, "_daily": daily}
    except Exception as e:
        print(f"[fetch_weather] {e}")
        return {"temp": "N/A", "condition": "Weather unavailable", "_daily": []}


def fetch_country_profile(country_name: str, country_code: str = "") -> dict:
    """Retrieve country intelligence, capital, region, and currency."""
    code_match = COUNTRY_DATA.get(country_code.upper()) if country_code else None
    if code_match:
        return code_match.copy()

    if country_name:
        name_key = country_name.lower().strip()
        name_match = COUNTRY_NAME_INDEX.get(name_key)
        if name_match:
            return name_match.copy()
        for k, v in COUNTRY_NAME_INDEX.items():
            if k in name_key or name_key in k:
                return v.copy()

    # Graceful fallback for any other country
    clean_name = country_name.title() if country_name else "Destination Area"
    return {
        "country": clean_name,
        "region": "International",
        "subregion": "",
        "capital": "Major Hub",
        "currencyCode": country_code.upper() if len(country_code) == 3 else "USD",
        "currencyName": "Local Currency",
        "currencySymbol": "",
        "flag": "🌍",
    }


def fetch_currency_conversion(amount: int, currency_code: str) -> dict:
    """Convert budget in INR to destination local currency."""
    if amount <= 0 or not currency_code or currency_code.upper() == "INR":
        return {"base": "INR", "target": currency_code or "INR", "rate": 1.0, "converted": amount}

    target = currency_code.upper()
    try:
        r = api_get(
            "https://api.frankfurter.app/latest",
            params={"from": "INR", "to": target},
            timeout=5,
        )
        if r.status_code == 200:
            data = r.json()
            rate = data.get("rates", {}).get(target)
            if rate:
                return {
                    "base": "INR",
                    "target": target,
                    "rate": rate,
                    "converted": round(amount * rate, 2),
                }
    except Exception as e:
        print(f"[currency_conversion frankfurter] {e}")

    # Fallback rate lookup
    fallback_rate = FALLBACK_INR_RATES.get(target)
    if fallback_rate:
        return {
            "base": "INR",
            "target": target,
            "rate": fallback_rate,
            "converted": round(amount * fallback_rate, 2),
        }

    return {"base": "INR", "target": target, "rate": None, "converted": None}


def search_nominatim_places(query: str, limit: int = 8) -> list:
    """Search points of interest via Nominatim."""
    places = []
    try:
        r = api_get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": query,
                "format": "jsonv2",
                "limit": limit,
                "addressdetails": 1,
                "accept-language": "en",
            },
            timeout=6,
        )
        if r.status_code == 200:
            for item in r.json():
                name = item.get("name") or (item.get("display_name") or "").split(",")[0].strip()
                try:
                    p_lat = float(item["lat"])
                    p_lon = float(item["lon"])
                except (ValueError, TypeError):
                    continue
                if name and not any(p["name"].lower() == name.lower() for p in places):
                    kind = (item.get("type") or item.get("category") or "attraction").replace("_", " ").title()
                    places.append({
                        "name": name,
                        "kinds": kind.lower().replace(" ", "_"),
                        "rate": 2,
                        "point": {"lat": p_lat, "lon": p_lon},
                        "address": item.get("display_name", ""),
                    })
    except Exception as e:
        print(f"[nominatim_places] {e}")
    return places


# ── Tour Guide Authority: Curated Landmarks for World Top Destinations ────
FAMOUS_DESTINATION_GUIDES = {
    "amritsar": [
        {
            "name": "Golden Temple (Sri Harmandir Sahib)",
            "kinds": "historic,spiritual",
            "point": {"lat": 31.6200, "lon": 74.8765},
            "description": "The holiest gurdwara of Sikhism. A breathtaking gilded marble sanctum surrounded by the sacred Amrit Sarovar (Pool of Nectar), welcoming all souls.",
            "tip": "Witness the morning/night Palki Sahib ceremony and experience the 24/7 community Langar serving over 100,000 visitors daily.",
        },
        {
            "name": "Jallianwala Bagh National Memorial",
            "kinds": "historic,memorial",
            "point": {"lat": 31.6206, "lon": 74.8801},
            "description": "Sacred national memorial garden commemorating martyrs of the 1919 massacre. Features the historic bullet-pitted red brick walls, Martyrs' Well, and the Eternal Flame.",
            "tip": "Located just 200m from the Golden Temple. Enter through the narrow historic alleyway.",
        },
        {
            "name": "Attari-Wagah Border Beating Retreat Ceremony",
            "kinds": "cultural,patriotic",
            "point": {"lat": 31.6048, "lon": 74.5714},
            "description": "World-famous daily military drill performed at dusk by India's Border Security Force and Pakistan Rangers with high kicks, patriotic cheering, and formal flag lowering.",
            "tip": "Leave the city by 2:30 PM to secure prime grandstand seats before the 4:45 PM ceremony begins.",
        },
        {
            "name": "Partition Museum (Town Hall)",
            "kinds": "museum,cultural",
            "point": {"lat": 31.6247, "lon": 74.8778},
            "description": "The world's first museum dedicated to the 1947 Partition of the Indian subcontinent, housing poignant oral histories, refugee archives, and preserved personal artifacts.",
            "tip": "Set aside at least 90 minutes to experience the compelling audio-visual galleries.",
        },
        {
            "name": "Gobindgarh Fort & Heritage Center",
            "kinds": "historic,fort",
            "point": {"lat": 31.6288, "lon": 74.8569},
            "description": "Magnificent 18th-century military stronghold fortified by Maharaja Ranjit Singh. Houses the historic Toshakhana treasury, warfare museum, and immersive cultural shows.",
            "tip": "Stay for the evening 'Sher-e-Punjab' laser projection mapping show illuminating the ancient fort walls.",
        },
        {
            "name": "Durgiana Temple (Shri Lakshmi Narayan Mandir)",
            "kinds": "spiritual,architecture",
            "point": {"lat": 31.6318, "lon": 74.8660},
            "description": "Premier Hindu temple architecturally inspired by the Golden Temple, featuring intricately carved silver doors and gilded domes rising gracefully above a sacred sarovar lake.",
            "tip": "Also lovingly called the 'Silver Temple'. Serene for an afternoon contemplation walk.",
        },
        {
            "name": "Heritage Street & Katra Jaimal Singh Market",
            "kinds": "marketplace,culinary",
            "point": {"lat": 31.6235, "lon": 74.8770},
            "description": "Vibrant pedestrian heritage promenade illuminated at twilight, flanked by traditional Rajput-Mughal facades, world-famous Amritsari Kulcha hotspots, and authentic Phulkari silk bazaars.",
            "tip": "Savor authentic stuffed kulchas with chilled sweet lassi at century-old dhabas nearby.",
        },
        {
            "name": "Ram Bagh & Maharaja Ranjit Singh Museum",
            "kinds": "historic,museum",
            "point": {"lat": 31.6375, "lon": 74.8785},
            "description": "Lush royal summer palace complex of the Lion of Punjab, featuring shaded garden walks, historic weaponry collections, and royal Sikh empire miniature artworks.",
            "tip": "Great relaxing midday stop away from the bustle of the old city.",
        },
    ],
    "agra": [
        {
            "name": "Taj Mahal",
            "kinds": "historic,wonder",
            "point": {"lat": 27.1751, "lon": 78.0421},
            "description": "UNESCO World Heritage wonder of the world. An ivory-white marble mausoleum on the south bank of the Yamuna river, commissioned by Mughal emperor Shah Jahan.",
            "tip": "Visit right at sunrise for golden reflection over the marble domes without crowds.",
        },
        {
            "name": "Agra Fort (Lal Qila)",
            "kinds": "historic,fort",
            "point": {"lat": 27.1795, "lon": 78.0211},
            "description": "Historic red sandstone fortress served as the main imperial residence of the Mughal emperors until 1638. Features the Diwan-i-Khas, Jahangir Palace, and Musamman Burj.",
            "tip": "Gaze across the Yamuna from the Musamman Burj where Shah Jahan spent his final years gazing at the Taj.",
        },
        {
            "name": "Mehtab Bagh (Moonlight Garden)",
            "kinds": "viewpoint,garden",
            "point": {"lat": 27.1800, "lon": 78.0420},
            "description": "Charbagh complex situated north of the Taj Mahal across the Yamuna River, offering iconic unobstructed sunset silhouette panoramas.",
            "tip": "Perfect sunset photo spot as the setting sun paints the Taj Mahal in rose-gold hues.",
        },
        {
            "name": "Fatehpur Sikri Imperial Complex",
            "kinds": "historic,unesco",
            "point": {"lat": 27.0945, "lon": 77.6679},
            "description": "Splendid red sandstone imperial ghost city founded by Emperor Akbar in 1571, home to the towering Buland Darwaza and Tomb of Salim Chishti.",
            "tip": "Located 36 km west of Agra; plan a half-day excursion here.",
        },
        {
            "name": "Tomb of I'timād-ud-Daulah (Baby Taj)",
            "kinds": "historic,architecture",
            "point": {"lat": 27.1929, "lon": 78.0310},
            "description": "Exquisite jewel-box mausoleum regarded as the stylistic architectural forerunner and inspiration for the Taj Mahal.",
            "tip": "Admire the delicate pietra dura gemstone inlays up close.",
        },
        {
            "name": "Sadar Bazaar & Kinari Bazaar",
            "kinds": "marketplace,culinary",
            "point": {"lat": 27.1601, "lon": 78.0081},
            "description": "Lively commercial heart of Agra famous for Agra Petha sweets, marble inlay souvenirs, leather craft, and chaat street food.",
            "tip": "Taste authentic Angoori and Kesar Petha from Panchhi Petha.",
        },
    ],
    "jaipur": [
        {
            "name": "Amber Palace (Amer Fort)",
            "kinds": "historic,fort",
            "point": {"lat": 26.9855, "lon": 75.8513},
            "description": "Stupendous hilltop fort blending Rajput and Mughal architecture, famed for the mirror-mosaic Sheesh Mahal, Maota Lake reflections, and royal courtyards.",
            "tip": "Arrive early morning or book an evening pass to witness the palace illuminated under stars.",
        },
        {
            "name": "Hawa Mahal (Palace of Winds)",
            "kinds": "historic,architecture",
            "point": {"lat": 26.9239, "lon": 75.8267},
            "description": "Iconic five-story pink sandstone honeycomb facade with 953 jharokha latticed windows designed to let royal ladies observe street festivals unseen.",
            "tip": "Head to the rooftop cafes opposite Hawa Mahal for the best photo angles with morning light.",
        },
        {
            "name": "City Palace of Jaipur",
            "kinds": "historic,palace",
            "point": {"lat": 26.9258, "lon": 75.8237},
            "description": "Royal residence of the Maharaja of Jaipur, featuring the Peacock Courtyard, Chandra Mahal, royal armoury, and Mubarak Mahal textile museum.",
            "tip": "Don't miss the four magnificent seasonal gate carvings in Pritam Niwas Chowk.",
        },
        {
            "name": "Jantar Mantar Astronomical Observatory",
            "kinds": "historic,science",
            "point": {"lat": 26.9248, "lon": 75.8246},
            "description": "UNESCO World Heritage collection of nineteen architectural astronomical instruments built by Rajput King Sawai Jai Singh II, including the world's largest stone sundial.",
            "tip": "Hire an authorized audio guide to understand how ancient astronomers measured time down to 2 seconds.",
        },
        {
            "name": "Nahargarh Fort & Sunset Point",
            "kinds": "viewpoint,fort",
            "point": {"lat": 26.9373, "lon": 75.8155},
            "description": "Formidable ridge fort crowning the Aravalli hills with sweeping panoramic views overlooking the entire Pink City.",
            "tip": "The ultimate sunset hangout; catch the city lights turning on across Jaipur below.",
        },
        {
            "name": "Jal Mahal (Water Palace)",
            "kinds": "sight,architecture",
            "point": {"lat": 26.9535, "lon": 75.8462},
            "description": "Picturesque palace submerged gracefully in the waters of Man Sagar Lake, surrounded by the Aravalli hills.",
            "tip": "Stroll the lakeside promenade at dusk when the palace shines with warm gold spotlights.",
        },
    ],
    "delhi": [
        {
            "name": "Red Fort (Lal Qila)",
            "kinds": "historic,unesco",
            "point": {"lat": 28.6562, "lon": 77.2410},
            "description": "Historic red sandstone fortress built by Mughal Emperor Shah Jahan in 1638, centerpiece of Old Delhi and symbol of Indian independence.",
            "tip": "Enter via the majestic Lahori Gate and explore Chhatta Chowk covered bazaar.",
        },
        {
            "name": "Qutub Minar & Mehrauli Archaeological Park",
            "kinds": "historic,unesco",
            "point": {"lat": 28.5245, "lon": 77.1855},
            "description": "World's tallest brick minaret standing at 72.5 meters, surrounded by ancient Islamic monuments and the 1600-year-old rust-resistant Iron Pillar of Delhi.",
            "tip": "Marvel at the intricate Quranic calligraphy carved onto alternating fluted stone tiers.",
        },
        {
            "name": "Humayun's Tomb & Sunder Nursery",
            "kinds": "historic,garden",
            "point": {"lat": 28.5933, "lon": 77.2507},
            "description": "Magnificent garden tomb commissioned by Empress Bega Begum, landmark synthesis of Persian and Indian architecture that inspired the Taj Mahal.",
            "tip": "Combine with a peaceful walk in the adjoining restored Sunder Nursery Mughal gardens.",
        },
        {
            "name": "India Gate & Kartavya Path",
            "kinds": "historic,memorial",
            "point": {"lat": 28.6129, "lon": 77.2295},
            "description": "Ceremonial 42-meter triumphal war memorial arch honoring 84,000 soldiers of the British Indian Army, anchoring the grand national boulevard.",
            "tip": "Lively evening atmosphere with fountains, ice cream carts, and views toward Rashtrapati Bhavan.",
        },
        {
            "name": "Lotus Temple (Bahá'í House of Worship)",
            "kinds": "spiritual,architecture",
            "point": {"lat": 28.5535, "lon": 77.2588},
            "description": "Architectural marvel shaped like an unfolding white marble lotus flower with 27 free-standing petals, welcoming people of all faiths to meditate in silence.",
            "tip": "Enjoy the tranquil reflecting ponds surrounding the main auditorium.",
        },
        {
            "name": "Chandni Chowk & Jama Masjid",
            "kinds": "cultural,culinary",
            "point": {"lat": 28.6507, "lon": 77.2334},
            "description": "Vibrant heart of Shahjahanabad; home to India's largest historic mosque Jama Masjid, fragrant spice alleys of Khari Baoli, and Paranthe Wali Gali.",
            "tip": "Take a cycle rickshaw through the narrow spice market for an unforgettable sensory journey.",
        },
    ],
    "goa": [
        {
            "name": "Fort Aguada & Portuguese Lighthouse",
            "kinds": "historic,viewpoint",
            "point": {"lat": 15.4920, "lon": 73.7737},
            "description": "Well-preserved 17th-century Portuguese fortress overlooking the Arabian Sea and Mandovi River confluence, built to protect Goa from Dutch and Maratha fleets.",
            "tip": "Stunning sunset cliff views over Sinquerim beach.",
        },
        {
            "name": "Basilica of Bom Jesus (Old Goa)",
            "kinds": "historic,unesco",
            "point": {"lat": 15.5009, "lon": 73.9116},
            "description": "UNESCO World Heritage baroque church enshrining the sacred mortal remains of Saint Francis Xavier, one of the oldest churches in India.",
            "tip": "Cross the road to admire the imposing Se Cathedral, the largest church in Asia.",
        },
        {
            "name": "Baga & Calangute Beachfront",
            "kinds": "beach,coastal",
            "point": {"lat": 15.5553, "lon": 73.7517},
            "description": "Goa's energetic beach strip renowned for water sports like parasailing and jet-skiing, bustling seaside shacks, and live music nightlife.",
            "tip": "Dine with your toes in the sand at candlelit beach shacks serving Goan fish curry.",
        },
        {
            "name": "Dudhsagar Waterfalls & Jungle Trek",
            "kinds": "natural,adventure",
            "point": {"lat": 15.3144, "lon": 74.3143},
            "description": "Four-tiered 'Sea of Milk' cascade plunging 310 meters down the Western Ghats jungle, crossed by the dramatic railway viaduct.",
            "tip": "Take a 4x4 jeep safari through Bhagwan Mahaveer Wildlife Sanctuary to reach the natural pool.",
        },
        {
            "name": "Chapora Fort & Vagator Sunset Cliff",
            "kinds": "historic,viewpoint",
            "point": {"lat": 15.6059, "lon": 73.7380},
            "description": "Iconic red laterite hilltop ramparts ('Dil Chahta Hai' fort) commanding sweeping vistas of Vagator and Morjim beaches and the Chapora river mouth.",
            "tip": "Bring comfortable walking shoes for the 10-minute climb up the rocky hill.",
        },
        {
            "name": "Fontainhas Latin Quarter (Panaji)",
            "kinds": "cultural,historic",
            "point": {"lat": 15.4989, "lon": 73.8278},
            "description": "Charming historic Portuguese quarter featuring pastel-colored heritage villas with tiled roofs, wrought-iron balconies, art galleries, and bakeries.",
            "tip": "Sample fresh Bebinca and warm pastéis de nata at traditional heritage bakeries.",
        },
    ],
    "varanasi": [
        {
            "name": "Dashashwamedh Ghat & Evening Ganga Aarti",
            "kinds": "spiritual,cultural",
            "point": {"lat": 25.3059, "lon": 83.0104},
            "description": "The main and oldest ghat on the sacred Ganges river, where saffron-robed priests perform the synchronized choreographed Maha Aarti every evening at twilight.",
            "tip": "Rent a wooden boat on the river by 6:00 PM for the most spellbinding view of the flaming brass lamps.",
        },
        {
            "name": "Kashi Vishwanath Temple (Golden Temple of Shiva)",
            "kinds": "spiritual,historic",
            "point": {"lat": 25.3109, "lon": 83.0107},
            "description": "One of the twelve revered Jyotirlingas, featuring golden spires and the majestic new corridor leading directly down to the holy riverfront.",
            "tip": "Deposit electronics in the locker facilities before entering through the secured corridor.",
        },
        {
            "name": "Assi Ghat Sunrise Boat Cruise & Morning Aarti",
            "kinds": "scenic,spiritual",
            "point": {"lat": 25.2891, "lon": 83.0067},
            "description": "Southernmost major ghat hosting the peaceful 'Subah-e-Banaras' morning music, classical yoga, and tranquil sunrise wooden boat cruises along the crescent ghats.",
            "tip": "Wake up at 5:30 AM to watch the sun rise out of the misty river as temple bells chime.",
        },
        {
            "name": "Sarnath Deer Park & Dhamek Stupa",
            "kinds": "historic,unesco",
            "point": {"lat": 25.3811, "lon": 83.0232},
            "description": "Sacred Buddhist pilgrimage site where Lord Buddha gave his first sermon setting the Wheel of Dharma in motion. Features the 43-meter cylindrical Dhamek Stupa.",
            "tip": "Visit the nearby Sarnath Archaeological Museum housing the original Ashokan Lion Capital (India's national emblem).",
        },
    ],
    "mumbai": [
        {
            "name": "Gateway of India & Taj Mahal Palace",
            "kinds": "historic,coastal",
            "point": {"lat": 18.9220, "lon": 72.8347},
            "description": "Monumental 26-meter basalt triumphal arch facing the Mumbai Harbour, built to commemorate King George V, flanked by the legendary 1903 Taj Mahal Palace hotel.",
            "tip": "Take scenic ferry rides right from the harbor jetty toward Elephanta Island.",
        },
        {
            "name": "Marine Drive Promenade (Queen's Necklace)",
            "kinds": "scenic,coastal",
            "point": {"lat": 18.9432, "lon": 72.8230},
            "description": "World-famous 3.6-kilometer C-shaped coastal boulevard along Netaji Subhash Chandra Bose Road, illuminated at night like a sparkling string of pearls.",
            "tip": "Sit on the tetrapod seawall at sunset and feel the cool Arabian Sea breeze.",
        },
        {
            "name": "Chhatrapati Shivaji Maharaj Terminus (CSMT)",
            "kinds": "historic,unesco",
            "point": {"lat": 18.9398, "lon": 72.8354},
            "description": "UNESCO World Heritage masterpiece of Victorian Gothic Revival architecture blended with traditional Indian motifs, stone domes, turrets, and stained glass.",
            "tip": "Gaze at the exterior facade at night when dynamic color-changing floodlights illuminate every detail.",
        },
        {
            "name": "Elephanta Caves Island",
            "kinds": "historic,unesco",
            "point": {"lat": 18.9633, "lon": 72.9315},
            "description": "Rock-cut cave temples dating to the 5th to 7th centuries carved into basalt cliffs on Gharapuri Island, famous for the magnificent 20-foot three-headed Maheshmurti Shiva sculpture.",
            "tip": "Enjoy the 1-hour ferry boat ride across Mumbai harbour to reach the island.",
        },
    ],
    "manali": [
        {
            "name": "Solang Valley Adventure Valley",
            "kinds": "natural,adventure",
            "point": {"lat": 32.3160, "lon": 77.1575},
            "description": "High-altitude paradise surrounded by snow-capped Himalayan peaks, offering paragliding, zorbing, quad biking, and winter skiing slopes.",
            "tip": "Take the scenic cable car ropeway to Mount Phatru for 360-degree glaciated mountain vistas.",
        },
        {
            "name": "Hadimba Devi Forest Temple",
            "kinds": "historic,spiritual",
            "point": {"lat": 32.2483, "lon": 77.1812},
            "description": "Unique 16th-century four-tiered pagoda-style wooden temple nestled inside the tranquil Dhungri cedar and deodar pine forests.",
            "tip": "Take peaceful woodland walks beneath towering 200-year-old cedar trees.",
        },
        {
            "name": "Atal Tunnel & Sissu Lahaul Valley",
            "kinds": "sight,adventure",
            "point": {"lat": 32.3644, "lon": 77.1333},
            "description": "World's longest highway tunnel above 10,000 feet connecting Manali to the breathtaking high-altitude Tibetan landscape of Lahaul and Sissu waterfall.",
            "tip": "The landscape transforms dramatically from lush green valley to rugged barren snow peaks as you exit the north portal.",
        },
        {
            "name": "Old Manali Village & Riverside Cafes",
            "kinds": "cultural,culinary",
            "point": {"lat": 32.2562, "lon": 77.1770},
            "description": "Rustic Himalayan village with traditional wooden houses, apple orchards, live acoustic music cafes, and artisan craft shops alongside the rushing Manalsu river.",
            "tip": "Try freshly baked trout fish and wood-fired pizzas at cozy bohemian cafes.",
        },
    ],
    "paris": [
        {
            "name": "Eiffel Tower (Tour Eiffel)",
            "kinds": "historic,landmark",
            "point": {"lat": 48.8584, "lon": 2.2945},
            "description": "World-renowned 330-meter wrought-iron lattice tower on the Champ de Mars, the universal symbol of France and romance.",
            "tip": "Watch the tower sparkle for 5 minutes at the beginning of every hour after dusk.",
        },
        {
            "name": "Louvre Museum & Glass Pyramid",
            "kinds": "museum,historic",
            "point": {"lat": 48.8606, "lon": 2.3376},
            "description": "The world's most visited art museum, housing over 35,000 masterpieces including Leonardo da Vinci's Mona Lisa, Venus de Milo, and Winged Victory of Samothrace.",
            "tip": "Book the earliest morning time slot and enter via the Carrousel du Louvre underground mall to beat main pyramid queues.",
        },
        {
            "name": "Cathédrale Notre-Dame de Paris",
            "kinds": "historic,architecture",
            "point": {"lat": 48.8530, "lon": 2.3499},
            "description": "Masterpiece of French Gothic architecture on the Île de la Cité, famous for its flying buttresses, twin bell towers, and majestic rose windows.",
            "tip": "Stroll around the island perimeter to admire the newly restored spire and medieval quays.",
        },
        {
            "name": "Arc de Triomphe & Champs-Élysées",
            "kinds": "historic,monument",
            "point": {"lat": 48.8738, "lon": 2.2950},
            "description": "Iconic triumphal arch honoring those who fought for France, anchoring twelve radiating avenues including the glamorous Avenue des Champs-Élysées.",
            "tip": "Climb the 284 steps to the roof terrace for breathtaking views directly down the twelve grand avenues.",
        },
        {
            "name": "Montmartre & Basilique du Sacré-Cœur",
            "kinds": "cultural,viewpoint",
            "point": {"lat": 48.8867, "lon": 2.3431},
            "description": "Charming hilltop bohemian village where Picasso and Van Gogh painted, crowned by the radiant white Romano-Byzantine Sacré-Cœur basilica overlooking all of Paris.",
            "tip": "Browse street portrait painters in Place du Tertre and catch sunset on the basilica steps.",
        },
    ],
    "tokyo": [
        {
            "name": "Sensō-ji Temple & Nakamise-dōri (Asakusa)",
            "kinds": "historic,spiritual",
            "point": {"lat": 35.7148, "lon": 139.7967},
            "description": "Tokyo's oldest and most significant Buddhist temple founded in 645 AD, entered through the monumental Kaminarimon Thunder Gate with its giant red lantern.",
            "tip": "Sample fresh ningyo-yaki bean-paste cakes along the historic Nakamise market street.",
        },
        {
            "name": "Shibuya Crossing & Hachiko Memorial",
            "kinds": "cultural,sight",
            "point": {"lat": 35.6595, "lon": 139.7004},
            "description": "The world's busiest pedestrian scramble crossing where up to 3,000 people cross in sync every green light amid towering neon screens.",
            "tip": "Head up to the Shibuya Sky rooftop observation deck for an unbelievable bird's-eye view of Tokyo.",
        },
        {
            "name": "Meiji Jingu Shrine & Yoyogi Forest",
            "kinds": "spiritual,natural",
            "point": {"lat": 35.6764, "lon": 139.6993},
            "description": "Tranquil Shinto shrine dedicated to Emperor Meiji, hidden within a lush 170-acre evergreen forest of 120,000 trees right in the center of Tokyo.",
            "tip": "Walk under the massive cypress Torii gate and see the colorful rows of donated sake barrels.",
        },
        {
            "name": "Tokyo Skytree",
            "kinds": "viewpoint,architecture",
            "point": {"lat": 35.7100, "lon": 139.8107},
            "description": "World's tallest free-standing broadcasting tower soaring 634 meters into the skyline, offering dizzying panoramas extending all the way to Mount Fuji on clear days.",
            "tip": "Book observation deck tickets at sunset to see Tokyo transition from day into a glittering neon sea.",
        },
    ],
    "rome": [
        {
            "name": "Colosseum (Flavian Amphitheatre)",
            "kinds": "historic,unesco",
            "point": {"lat": 41.8902, "lon": 12.4922},
            "description": "The largest ancient amphitheatre ever built, capable of holding 50,000 spectators for gladiatorial contests and public spectacles in imperial Rome.",
            "tip": "Book a combined Colosseum, Roman Forum, and Palatine Hill ticket in advance.",
        },
        {
            "name": "Vatican Museums & St. Peter's Basilica",
            "kinds": "historic,museum",
            "point": {"lat": 41.9029, "lon": 12.4534},
            "description": "Epic spiritual headquarters featuring Michelangelo's legendary Sistine Chapel ceiling and St. Peter's, the grandest Renaissance church on Earth.",
            "tip": "Climb up to the dome of St. Peter's for an unforgettable view over St. Peter's Square.",
        },
        {
            "name": "Trevi Fountain (Fontana di Trevi)",
            "kinds": "historic,monument",
            "point": {"lat": 41.9009, "lon": 12.4833},
            "description": "Rome's most famous baroque fountain designed by Nicola Salvi, depicting the Greek Titan Oceanus flanked by tritons and sea horses.",
            "tip": "Toss a coin with your right hand over your left shoulder to ensure you will one day return to Rome.",
        },
        {
            "name": "The Pantheon & Piazza della Rotonda",
            "kinds": "historic,architecture",
            "point": {"lat": 41.8986, "lon": 12.4769},
            "description": "The world's best-preserved Roman monument with its colossal unreinforced concrete dome and 9-meter open oculus illuminating the interior.",
            "tip": "Grab an authentic espresso or gelato at Piazza Navona nearby after visiting.",
        },
    ],
    "new york": [
        {
            "name": "Statue of Liberty & Ellis Island",
            "kinds": "historic,memorial",
            "point": {"lat": 40.6892, "lon": -74.0445},
            "description": "Iconic neoclassical colossal copper statue on Liberty Island, gifted by France in 1886 as a universal beacon of freedom and democracy.",
            "tip": "Take the morning ferry from Battery Park to explore both Liberty and Ellis Island museums.",
        },
        {
            "name": "Central Park",
            "kinds": "natural,park",
            "point": {"lat": 40.7851, "lon": -73.9683},
            "description": "843-acre urban oasis in Manhattan featuring Bethesda Terrace, Bow Bridge, Sheep Meadow, The Ramble woodland trails, and Strawberry Fields.",
            "tip": "Rent a rowboat at the Central Park Loeb Boathouse for an iconic New York afternoon.",
        },
        {
            "name": "Empire State Building & Observatory",
            "kinds": "viewpoint,architecture",
            "point": {"lat": 40.7484, "lon": -73.9857},
            "description": "Legendary 102-story Art Deco skyscraper in Midtown Manhattan, offering 360-degree open-air deck panoramas stretching across five states.",
            "tip": "Visit late evening when the skyline illuminates and queues subside.",
        },
        {
            "name": "Times Square & Broadway Theater District",
            "kinds": "cultural,entertainment",
            "point": {"lat": 40.7580, "lon": -73.9855},
            "description": "The electrifying 'Crossroads of the World' illuminated by towering digital billboards, street performers, and world-class Broadway theaters.",
            "tip": "Check the TKTS red stairs booth for same-day discounted Broadway show tickets.",
        },
    ],
    "dubai": [
        {
            "name": "Burj Khalifa Observation Deck",
            "kinds": "viewpoint,architecture",
            "point": {"lat": 25.1972, "lon": 55.2744},
            "description": "The world's tallest building soaring 828 meters high, featuring high-speed observation lifts and mind-boggling vistas over the Dubai desert and Arabian Gulf.",
            "tip": "Book the 'At the Top' ticket for levels 124 & 125 during sunset hour.",
        },
        {
            "name": "The Dubai Mall & Dubai Fountain Show",
            "kinds": "marketplace,entertainment",
            "point": {"lat": 25.1985, "lon": 55.2796},
            "description": "World's largest shopping and entertainment destination, featuring an Olympic ice rink, giant aquarium, and the choreographed Dubai Fountain show.",
            "tip": "Watch the dancing fountain show every 30 minutes in the evening with Burj Khalifa illuminated.",
        },
        {
            "name": "Palm Jumeirah & The View at The Palm",
            "kinds": "sight,coastal",
            "point": {"lat": 25.1124, "lon": 55.1390},
            "description": "Famous man-made palm-tree-shaped archipelago jutting into the Arabian Gulf, crowned by Atlantis The Palm resort and Aquaventure Waterpark.",
            "tip": "Ride the Palm Monorail from the gateway up to the Atlantis crescent.",
        },
    ],
    "bali": [
        {
            "name": "Tanah Lot Sea Temple",
            "kinds": "spiritual,coastal",
            "point": {"lat": -8.6212, "lon": 115.0868},
            "description": "Ancient Hindu sea temple perched dramatically atop an offshore rock formation carved by ocean tides, dedicated to the guardian sea gods.",
            "tip": "Unforgettable at sunset as the waves crash against the sea shrine silhouette.",
        },
        {
            "name": "Ubud Sacred Monkey Forest Sanctuary",
            "kinds": "natural,cultural",
            "point": {"lat": -8.5188, "lon": 115.2588},
            "description": "Mystical sacred nature sanctuary and temple complex home to over 1,000 Balinese long-tailed macaques nestled inside ancient mossy banyan forests.",
            "tip": "Keep loose items, sunglasses, and snacks securely zipped inside your bag.",
        },
        {
            "name": "Tegallalang Rice Terraces",
            "kinds": "natural,scenic",
            "point": {"lat": -8.4312, "lon": 115.2789},
            "description": "Breathtaking emerald-green stepped rice paddies carved into river valleys using the UNESCO-recognized traditional Balinese Subak irrigation system.",
            "tip": "Explore early in the morning when the sun casts golden light through palm canopies.",
        },
        {
            "name": "Uluwatu Temple & Sunset Kecak Fire Dance",
            "kinds": "spiritual,cultural",
            "point": {"lat": -8.8291, "lon": 115.0849},
            "description": "Magnificent cliffside temple perched 70 meters above roaring Indian Ocean waves, famous for its daily sunset Kecak fire and trance dance performance.",
            "tip": "Buy Kecak dance tickets by 4:30 PM as the outdoor amphitheatre sells out rapidly.",
        },
    ],
}


def fetch_wikipedia_attractions(destination: str, lat: float, lon: float, needed: int = 8) -> list:
    """Discover authentic landmark attractions and real descriptions via Wikipedia API."""
    places = []
    seen_titles = set()
    headers = {"User-Agent": "PlanoraTravelPlanner/1.0 (contact@planora.app)"}

    # Step 1: Wikipedia Geosearch around destination coordinates
    try:
        r = api_get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "generator": "geosearch",
                "ggscoord": f"{lat}|{lon}",
                "ggsradius": 12000,
                "ggslimit": 12,
                "prop": "coordinates|extracts|pageprops",
                "exintro": 1,
                "explaintext": 1,
                "exchars": 220,
                "format": "json",
                "utf8": 1,
            },
            headers=headers,
            timeout=5,
        )
        if r.status_code == 200:
            pages = r.json().get("query", {}).get("pages", {})
            for pid, p in pages.items():
                title = p.get("title", "").strip()
                coords = (p.get("coordinates") or [{}])[0]
                p_lat = coords.get("lat")
                p_lon = coords.get("lon")
                extract = (p.get("extract") or "").strip().replace("\n", " ")

                lower_title = title.lower()
                # Filter out administrative, transit, or non-tourist records
                if any(bad in lower_title for bad in [
                    "demographics", "climate of", "transport in", "district", "electoral",
                    "railway station", "airport", "expressway", "bypass", "list of", "constituency"
                ]):
                    continue
                if lower_title == destination.lower():
                    continue

                if title and lower_title not in seen_titles and p_lat is not None and p_lon is not None:
                    seen_titles.add(lower_title)
                    places.append({
                        "name": title,
                        "kinds": "landmark,historic",
                        "rate": 4,
                        "point": {"lat": p_lat, "lon": p_lon},
                        "description": extract,
                        "tip": "Prominent landmark highlighted in official city travel guides.",
                    })
    except Exception as e:
        print(f"[fetch_wikipedia_attractions geosearch] {e}")

    # Step 2: Wikipedia Search for 'tourist attractions in {destination}'
    if len(places) < needed:
        try:
            r = api_get(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": f"tourist attractions in {destination}",
                    "format": "json",
                    "utf8": 1,
                    "srlimit": 8,
                },
                headers=headers,
                timeout=5,
            )
            if r.status_code == 200:
                search_results = r.json().get("query", {}).get("search", [])
                candidate_titles = []
                for s in search_results:
                    t = s.get("title", "").strip()
                    lower_t = t.lower()
                    if (
                        lower_t.startswith("list of")
                        or lower_t == destination.lower()
                        or "tourism in" in lower_t
                        or any(bad in lower_t for bad in ["demographics", "climate", "history of"])
                    ):
                        continue
                    if lower_t not in seen_titles:
                        candidate_titles.append(t)

                if candidate_titles:
                    t_str = "|".join(candidate_titles[:6])
                    r_details = api_get(
                        "https://en.wikipedia.org/w/api.php",
                        params={
                            "action": "query",
                            "titles": t_str,
                            "prop": "coordinates|extracts",
                            "exintro": 1,
                            "explaintext": 1,
                            "exchars": 220,
                            "format": "json",
                            "utf8": 1,
                        },
                        headers=headers,
                        timeout=5,
                    )
                    if r_details.status_code == 200:
                        detail_pages = r_details.json().get("query", {}).get("pages", {})
                        for pid, p in detail_pages.items():
                            t = p.get("title", "").strip()
                            if not t or t.lower() in seen_titles:
                                continue
                            coords = (p.get("coordinates") or [{}])[0]
                            p_lat = coords.get("lat") or round(lat + ((hash(t) % 20) - 10) * 0.001, 5)
                            p_lon = coords.get("lon") or round(lon + ((hash(t[::-1]) % 20) - 10) * 0.001, 5)
                            extract = (p.get("extract") or "").strip().replace("\n", " ")
                            seen_titles.add(t.lower())
                            places.append({
                                "name": t,
                                "kinds": "sight,cultural",
                                "rate": 4,
                                "point": {"lat": p_lat, "lon": p_lon},
                                "description": extract,
                                "tip": "Popular sightseeing destination recommended by travel guides.",
                            })
        except Exception as e:
            print(f"[fetch_wikipedia_attractions search] {e}")

    return places


def generate_contextual_attractions(destination: str, lat: float, lon: float, count: int = 8) -> list:
    """Generate realistic contextual attractions around the destination coordinates."""
    templates = [
        (f"{destination} Historic Old Quarter", "historic", "Walk along traditional streets and discover neighborhood heritage and architecture.", 0.006, 0.005),
        (f"{destination} Central Promenade & Plaza", "plaza", "Vibrant central gathering square flanked by local cafes, monuments, and fountains.", -0.005, 0.007),
        (f"{destination} Heritage Museum & Gallery", "museum", "Cultural repository showcasing regional art, historical relics, and exhibitions.", 0.009, -0.006),
        (f"{destination} Scenic Waterfront & Viewpoint", "viewpoint", "Picturesque coastal/riverfront overlook with serene panoramic views.", -0.008, -0.009),
        (f"{destination} Botanical Gardens & Sanctuary", "natural", "Sprawling floral gardens and shaded nature paths for a tranquil afternoon retreat.", 0.013, 0.008),
        (f"{destination} Cultural Arts Landmark", "cultural", "Renowned regional arts hub celebrating local dance, music, and architectural heritage.", -0.011, 0.012),
        (f"{destination} Artisan Bazaar & Market", "marketplace", "Bustling traditional market filled with local crafts, textiles, and street delicacies.", 0.004, -0.010),
        (f"{destination} Panoramic Lookout Point", "viewpoint", "Elevated observation ridge offering breathtaking 360-degree skyline views.", -0.015, -0.004),
    ]
    results = []
    for name, kind, desc, dlat, dlon in templates[:count]:
        results.append({
            "name": name,
            "kinds": kind,
            "rate": 2,
            "point": {
                "lat": round(lat + dlat, 5),
                "lon": round(lon + dlon, 5),
            },
            "description": desc,
            "tip": "Great spot for photography and leisurely exploration.",
        })
    return results


def fetch_attractions(lat: float, lon: float, num_days: int, destination: str = "", stops_per_day: int = 3) -> list:
    """Discover attractions with Curated Tour Guide, Wikipedia, Nominatim, and contextual backup."""
    needed = max(12, num_days * stops_per_day + 5)
    places = []
    seen_names = set()

    # 1. Curated Tour Guide Authority (Highest reliability: Amritsar, Agra, Jaipur, Delhi, Goa, Paris, etc.)
    clean_dest = destination.lower()
    for guide_key, landmarks in FAMOUS_DESTINATION_GUIDES.items():
        if guide_key in clean_dest or clean_dest in guide_key:
            for lk in landmarks:
                name_key = lk["name"].lower()
                if name_key not in seen_names:
                    seen_names.add(name_key)
                    places.append({
                        "name": lk["name"],
                        "kinds": lk.get("kinds", "historic"),
                        "rate": 5,
                        "point": lk["point"],
                        "description": lk.get("description", ""),
                        "tip": lk.get("tip", ""),
                    })
            break

    # 2. Wikipedia API Live Discovery (Tour guide authenticity for any global city)
    if len(places) < needed and destination:
        wiki_places = fetch_wikipedia_attractions(destination, lat, lon, needed=(needed - len(places)))
        for wp in wiki_places:
            name_key = wp["name"].lower()
            if not any(name_key in sn or sn in name_key for sn in seen_names):
                seen_names.add(name_key)
                places.append(wp)

    # 3. OpenTripMap (if key configured)
    if len(places) < needed and OPENTRIPMAP_KEY:
        try:
            r = api_get(
                "https://api.opentripmap.com/0.1/en/places/radius",
                params={
                    "radius": 15000,
                    "lon": lon,
                    "lat": lat,
                    "kinds": "interesting_places,historic,natural,cultural,architecture",
                    "format": "json",
                    "limit": needed,
                    "rate": 1,
                    "apikey": OPENTRIPMAP_KEY,
                },
                timeout=6,
            )
            if r.status_code == 200:
                for p in r.json():
                    p_name = p.get("name", "").strip()
                    if p_name and not any(p_name.lower() in sn for sn in seen_names):
                        seen_names.add(p_name.lower())
                        places.append(p)
        except Exception as e:
            print(f"[opentripmap] {e}")

    # 4. Nominatim Attraction Search
    if len(places) < needed and destination:
        osm_places = search_nominatim_places(f"attractions in {destination}", limit=6)
        for op in osm_places:
            name_key = op["name"].lower()
            if not any(name_key in sn or sn in name_key for sn in seen_names):
                seen_names.add(name_key)
                places.append(op)

    # 5. Fill with contextual attractions if needed
    if len(places) < needed:
        contextual = generate_contextual_attractions(
            destination.title() if destination else "Destination",
            lat, lon, count=(needed - len(places))
        )
        for cp in contextual:
            name_key = cp["name"].lower()
            if not any(name_key in sn for sn in seen_names):
                seen_names.add(name_key)
                places.append(cp)

    return places


def classify_attraction(place: dict) -> dict:
    """Determine indoor/outdoor nature and ideal time-of-day slot for an attraction."""
    text = f"{place.get('kinds', '')} {place.get('name', '')}".lower()
    indoor_keywords = ("museum", "gallery", "palace", "mall", "science", "cathedral", "aquarium", "theater", "cultural", "library")
    evening_keywords = ("sunset", "bazaar", "market", "night", "promenade", "lounge", "culinary", "times square", "fountain", "pier")
    morning_keywords = ("fort", "park", "garden", "natural", "viewpoint", "temple", "spiritual", "beach", "terrace", "sanctuary", "bridge")

    is_indoor = any(kw in text for kw in indoor_keywords)
    if any(kw in text for kw in evening_keywords):
        preferred_slot = "Evening"
    elif any(kw in text for kw in morning_keywords):
        preferred_slot = "Morning"
    else:
        preferred_slot = "Afternoon"

    return {"is_indoor": is_indoor, "preferred_slot": preferred_slot}


def cluster_attractions_by_day(
    attractions: list,
    num_days: int,
    stops_per_day: int,
    origin_lat: float,
    origin_lon: float,
    daily_weather: list,
) -> tuple:
    """
    Group attractions into geographic proximity clusters (1 per day),
    apply weather-reactive indoor prioritization for rainy days,
    and sequence stops within each day by time-of-day & nearest-neighbor routing.
    Returns (day_buckets, unused_pool).
    """
    if not attractions:
        return [[] for _ in range(num_days)], []

    # Sort primarily by authority rating so must-see sights stay in the active plan
    ranked = sorted(attractions, key=lambda x: x.get("rate", 0), reverse=True)
    active_limit = min(len(ranked), num_days * stops_per_day)
    active = ranked[:active_limit]
    unused_pool = ranked[active_limit:]

    # Annotate coordinates & metadata
    for p in active:
        pt = p.get("point", {})
        if pt.get("lat") is None or pt.get("lon") is None:
            p["point"] = {"lat": origin_lat, "lon": origin_lon}

    if num_days == 1 or len(active) <= stops_per_day:
        buckets = [active] + [[] for _ in range(num_days - 1)]
    else:
        # K-Means geographic district centroids (k = num_days)
        # Farthest-point seed initialization for clean spatial separation
        centroids = [(active[0]["point"]["lat"], active[0]["point"]["lon"])]
        for _ in range(1, num_days):
            best_pt = None
            best_dist = -1.0
            for cand in active:
                c_lat, c_lon = cand["point"]["lat"], cand["point"]["lon"]
                min_d = min(haversine_distance_km(c_lat, c_lon, cen[0], cen[1]) for cen in centroids)
                if min_d > best_dist:
                    best_dist = min_d
                    best_pt = (c_lat, c_lon)
            centroids.append(best_pt or (origin_lat, origin_lon))

        # 6 fast K-Means iterations
        for _ in range(6):
            temp_groups = [[] for _ in range(num_days)]
            for item in active:
                ilat, ilon = item["point"]["lat"], item["point"]["lon"]
                nearest_idx = min(
                    range(num_days),
                    key=lambda idx: haversine_distance_km(ilat, ilon, centroids[idx][0], centroids[idx][1]),
                )
                temp_groups[nearest_idx].append(item)
            for idx, grp in enumerate(temp_groups):
                if grp:
                    avg_lat = sum(x["point"]["lat"] for x in grp) / len(grp)
                    avg_lon = sum(x["point"]["lon"] for x in grp) / len(grp)
                    centroids[idx] = (avg_lat, avg_lon)

        # Balanced capacity assignment so every day receives balanced stops
        buckets = [[] for _ in range(num_days)]
        min_per_day = max(1, len(active) // num_days)
        max_per_day = min_per_day + (1 if len(active) % num_days else 0)
        unassigned = list(active)

        # First pass: assign closest items up to min_per_day
        for day_i in range(num_days):
            c_lat, c_lon = centroids[day_i]
            unassigned.sort(key=lambda x: haversine_distance_km(x["point"]["lat"], x["point"]["lon"], c_lat, c_lon))
            while len(buckets[day_i]) < min_per_day and unassigned:
                buckets[day_i].append(unassigned.pop(0))

        # Second pass: distribute remaining items to nearest day under max_per_day
        for item in unassigned:
            ilat, ilon = item["point"]["lat"], item["point"]["lon"]
            eligible = [i for i in range(num_days) if len(buckets[i]) < max_per_day]
            if not eligible:
                eligible = list(range(num_days))
            best_i = min(
                eligible,
                key=lambda idx: haversine_distance_km(ilat, ilon, centroids[idx][0], centroids[idx][1]),
            )
            buckets[best_i].append(item)

    # Weather-reactive swap: move indoor spots onto rainy days when clear days hold them
    if daily_weather and num_days > 1:
        rain_keywords = ("rain", "drizzle", "shower", "thunderstorm", "snow")
        rainy_days = [
            i for i in range(min(num_days, len(daily_weather)))
            if any(rk in (daily_weather[i].get("condition") or "").lower() for rk in rain_keywords)
        ]
        clear_days = [i for i in range(num_days) if i not in rainy_days]
        for r_idx in rainy_days:
            for c_idx in clear_days:
                indoor_in_clear = next((p for p in buckets[c_idx] if classify_attraction(p)["is_indoor"]), None)
                outdoor_in_rain = next((p for p in buckets[r_idx] if not classify_attraction(p)["is_indoor"]), None)
                if indoor_in_clear and outdoor_in_rain:
                    buckets[c_idx].remove(indoor_in_clear)
                    buckets[r_idx].remove(outdoor_in_rain)
                    buckets[r_idx].append(indoor_in_clear)
                    buckets[c_idx].append(outdoor_in_rain)

    # Intra-day ordering: Morning -> Afternoon -> Evening, breaking ties by nearest-neighbor path
    slot_rank = {"Morning": 0, "Afternoon": 1, "Evening": 2}
    ordered_buckets = []
    for grp in buckets:
        if len(grp) <= 1:
            ordered_buckets.append(grp)
            continue
        remaining = list(grp)
        ordered = []
        cur_lat, cur_lon = origin_lat, origin_lon
        while remaining:
            remaining.sort(
                key=lambda x: (
                    slot_rank.get(classify_attraction(x)["preferred_slot"], 1),
                    haversine_distance_km(cur_lat, cur_lon, x["point"]["lat"], x["point"]["lon"]),
                )
            )
            chosen = remaining.pop(0)
            ordered.append(chosen)
            cur_lat, cur_lon = chosen["point"]["lat"], chosen["point"]["lon"]
        ordered_buckets.append(ordered)

    return ordered_buckets, unused_pool


def get_cuisine_highlights(destination: str, day_idx: int, country_name: str = "") -> str:
    """Return authentic regional culinary highlight for the given destination & day."""
    clean = (destination or "").lower()
    for key, tips in DEST_CUISINE_TIPS.items():
        if key in clean:
            return tips[day_idx % len(tips)]
    defaults = [
        f"Try a traditional local breakfast dish or bakery specialty in {destination.title() or 'town'}.",
        f"Explore a bustling neighborhood market or authentic family-run restaurant for regional lunch.",
        f"Sample signature street food or an atmospheric evening cafe specialty.",
    ]
    if country_name:
        defaults[1] = f"Book or walk into a top-rated local spot serving authentic {country_name} cuisine."
    return defaults[day_idx % len(defaults)]


def enhance_itinerary_with_ai(
    itinerary: list,
    destination: str,
    travel_style: str,
    pace: str,
    budget_intel: dict,
) -> tuple:
    """
    Optionally enrich descriptions, insider tips, and meal recommendations
    using Gemini 2.0 Flash / Groq / OpenAI grounded strictly on real discovered stops.
    Falls back cleanly to the deterministic engine if no key is configured or on any failure.
    Returns (enhanced_itinerary, ai_powered_bool, model_name).
    """
    if not (GEMINI_API_KEY or GROQ_API_KEY or OPENAI_API_KEY):
        return itinerary, False, "Planora Smart Clustering v2 (Algorithmic)"

    compact_days = []
    for day in itinerary:
        stops = [
            {"title": act["title"], "time": act["time"]}
            for act in day.get("activities", [])
            if isinstance(act, dict)
        ]
        compact_days.append({"day": day["day"], "stops": stops})

    prompt = (
        f"You are an expert travel concierge for {destination}. "
        f"Traveler style: {travel_style}. Pace: {pace}. Budget level: {budget_intel.get('statusLabel', 'Moderate')}.\n"
        f"Enhance these EXACT verified daily itineraries without removing or inventing stop coordinates. "
        f"Return STRICT valid JSON only (no markdown fences) matching:\n"
        f'{{"days": [{{"day": 1, "theme": "Short punchy theme", "mealTip": "Specific iconic local food spot/dish to try", '
        f'"tips": ["One concise insider tip per stop in same order"]}}]}}\n'
        f"Input stops: {json.dumps(compact_days)}"
    )

    raw_text = ""
    model_used = ""
    try:
        if GEMINI_API_KEY:
            model_used = "Gemini 2.0 Flash (Grounded RAG)"
            resp = HTTP.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}",
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.4, "responseMimeType": "application/json"},
                },
                timeout=6,
            )
            if resp.status_code == 200:
                candidates = resp.json().get("candidates") or []
                if candidates:
                    raw_text = candidates[0]["content"]["parts"][0]["text"]
        elif GROQ_API_KEY:
            model_used = "Groq Llama 3.3 (Grounded RAG)"
            resp = HTTP.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.4,
                    "response_format": {"type": "json_object"},
                },
                timeout=6,
            )
            if resp.status_code == 200:
                raw_text = resp.json()["choices"][0]["message"]["content"]
        elif OPENAI_API_KEY:
            model_used = "GPT-4o Mini (Grounded RAG)"
            resp = HTTP.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.4,
                    "response_format": {"type": "json_object"},
                },
                timeout=6,
            )
            if resp.status_code == 200:
                raw_text = resp.json()["choices"][0]["message"]["content"]

        if raw_text:
            parsed = json.loads(raw_text)
            ai_days = {d.get("day"): d for d in (parsed.get("days") or [])}
            for day in itinerary:
                ai_day = ai_days.get(day["day"])
                if not ai_day:
                    continue
                if ai_day.get("theme"):
                    day["title"] = ai_day["theme"]
                if ai_day.get("mealTip"):
                    day["mealTip"] = ai_day["mealTip"]
                ai_tips = ai_day.get("tips") or []
                obj_idx = 0
                for act in day.get("activities", []):
                    if isinstance(act, dict):
                        if obj_idx < len(ai_tips) and ai_tips[obj_idx]:
                            act["tip"] = ai_tips[obj_idx]
                        obj_idx += 1
            return itinerary, True, model_used
    except Exception as e:
        print(f"[enhance_itinerary_with_ai fallback] {e}")

    return itinerary, False, "Planora Smart Clustering v2 (Algorithmic)"


def build_itinerary(
    attractions: list,
    num_days: int,
    start_date: str,
    daily_weather: list,
    origin_lat: float = 0.0,
    origin_lon: float = 0.0,
    destination: str = "",
    country_name: str = "",
    travel_style: str = "solo",
    pace: str = "balanced",
) -> tuple:
    """Organize attractions into spatially clustered, weather-aware daily itinerary cards."""
    pace_map = {"relaxed": 2, "balanced": 3, "packed": 4}
    stops_per_day = pace_map.get(pace, 3)

    day_buckets, unused_pool = cluster_attractions_by_day(
        attractions, num_days, stops_per_day, origin_lat, origin_lon, daily_weather
    )

    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    itinerary = []
    periods = ["Morning", "Afternoon", "Evening", "Late Evening"]

    for day_idx in range(num_days):
        day_places = day_buckets[day_idx] if day_idx < len(day_buckets) else []
        date_str = (start_dt + timedelta(days=day_idx)).strftime("%b %d")
        theme = DAY_THEMES[day_idx % len(DAY_THEMES)]

        activities = []
        place_coords = []

        if day_idx == 0:
            activities.append("Arrive, check in to your accommodation and get settled 🧳")

        for p_idx, place in enumerate(day_places):
            name = place.get("name", "").strip()
            kinds = place.get("kinds", "")
            label = kinds.split(",")[0].replace("_", " ").title() if kinds else "Sight"
            desc = place.get("description", "")
            tip = place.get("tip", "")
            meta = classify_attraction(place)
            time_slot = periods[p_idx] if p_idx < len(periods) else meta["preferred_slot"]
            pt = place.get("point", {})

            activities.append({
                "time": time_slot,
                "title": f"Explore {name}",
                "placeName": name,
                "label": label,
                "desc": desc,
                "tip": tip,
                "indoor": meta["is_indoor"],
                "lat": pt.get("lat"),
                "lon": pt.get("lon"),
            })

            if pt.get("lat") and pt.get("lon"):
                place_coords.append({"name": name, "lat": pt["lat"], "lon": pt["lon"]})

        if not activities:
            activities = FALLBACK_ACTIVITIES[day_idx % len(FALLBACK_ACTIVITIES)].copy()

        # Day weather forecast
        if daily_weather and day_idx < len(daily_weather):
            w = daily_weather[day_idx]
            if w.get("temp_max") is not None and w.get("temp_min") is not None:
                activities.append(
                    f"🌤️ Day Forecast: {w['condition']} — High: {w['temp_max']}°C / Low: {w['temp_min']}°C"
                )

        if day_idx == num_days - 1:
            activities.append("Souvenir shopping and departure transfer 🏠")

        itinerary.append({
            "day": day_idx + 1,
            "date": date_str,
            "title": theme,
            "mealTip": get_cuisine_highlights(destination, day_idx, country_name),
            "styleNote": TRAVEL_STYLE_NOTES.get(travel_style, "") if day_idx == 0 else "",
            "activities": activities,
            "places": place_coords,
        })

    # Serialize unused pool for instant client-side activity swapping
    serialized_unused = []
    for p in unused_pool:
        name = p.get("name", "").strip()
        kinds = p.get("kinds", "")
        pt = p.get("point", {})
        meta = classify_attraction(p)
        serialized_unused.append({
            "title": f"Explore {name}",
            "placeName": name,
            "label": kinds.split(",")[0].replace("_", " ").title() if kinds else "Sight",
            "desc": p.get("description", ""),
            "tip": p.get("tip", ""),
            "indoor": meta["is_indoor"],
            "lat": pt.get("lat"),
            "lon": pt.get("lon"),
        })

    return itinerary, serialized_unused


def enrich_itinerary_with_routes(itinerary: list, origin_lat: float, origin_lon: float) -> list:
    """Calculate driving distance and estimated time for daily itinerary stops."""
    for day in itinerary:
        coords = [[origin_lon, origin_lat]]
        for place in day.get("places", []):
            if place.get("lat") is not None and place.get("lon") is not None:
                coords.append([place["lon"], place["lat"]])

        if len(coords) < 2:
            day["routeSummary"] = None
            continue

        # Fast OSRM query attempt
        routed = False
        try:
            coord_string = ";".join(f"{lon},{lat}" for lon, lat in coords)
            r = api_get(
                f"https://router.project-osrm.org/trip/v1/driving/{coord_string}",
                params={"source": "first", "roundtrip": "false", "overview": "false"},
                timeout=3,
            )
            if r.status_code == 200:
                trip = (r.json().get("trips") or [{}])[0]
                dist_km = round((trip.get("distance") or 0) / 1000, 1)
                dur_min = round((trip.get("duration") or 0) / 60)
                if dist_km > 0:
                    day["routeSummary"] = {"distanceKm": dist_km, "durationMin": dur_min}
                    routed = True
        except Exception:
            routed = False

        if not routed:
            # Haversine distance with road curvature factor fallback
            total_dist = 0.0
            for i in range(len(coords) - 1):
                total_dist += haversine_distance_km(
                    coords[i][1], coords[i][0], coords[i + 1][1], coords[i + 1][0]
                )
            total_dist = max(1.5, round(total_dist * 1.3, 1))
            dur_min = max(10, round(total_dist / 35.0 * 60))
            day["routeSummary"] = {"distanceKm": total_dist, "durationMin": dur_min}

    return itinerary


def serialize_attractions(attractions: list) -> list:
    """Return attraction markers for map visualization."""
    markers = []
    for place in attractions:
        point = place.get("point", {})
        lat = point.get("lat")
        lon = point.get("lon")
        name = place.get("name", "").strip()
        if not name or lat is None or lon is None:
            continue

        kind = place.get("kinds", "").split(",")[0].replace("_", " ").title()
        markers.append({
            "name": name,
            "lat": lat,
            "lon": lon,
            "kind": kind or "Attraction",
        })
    return markers


def fetch_osm_hotels(destination: str, city_name: str, lat: float, lon: float) -> list:
    """Fetch hotel and accommodation suggestions."""
    hotels = []
    raw_places = search_nominatim_places(f"hotels in {destination}", limit=6)
    for p in raw_places:
        hotels.append({
            "name": p["name"],
            "type": "Hotel",
            "rating": "4.5★",
            "pricePerNight": None,
            "address": p.get("address", destination),
            "lat": p["point"]["lat"],
            "lon": p["point"]["lon"],
        })

    # Ensure at least 4 hotels exist
    if len(hotels) < 4:
        contextual = [
            {"name": f"The Grand {city_name} Hotel & Suites", "type": "Luxury Hotel", "rating": "4.7★", "dlat": 0.007, "dlon": 0.006},
            {"name": f"{city_name} Heritage Palace Resort", "type": "Resort", "rating": "4.6★", "dlat": -0.008, "dlon": 0.009},
            {"name": f"{city_name} Boutique Villa Stay", "type": "Boutique", "rating": "4.4★", "dlat": 0.010, "dlon": -0.007},
            {"name": f"Palm View Residency {city_name}", "type": "Guest House", "rating": "4.3★", "dlat": -0.009, "dlon": -0.008},
        ]
        for item in contextual:
            if not any(h["name"].lower() == item["name"].lower() for h in hotels):
                hotels.append({
                    "name": item["name"],
                    "type": item["type"],
                    "rating": item["rating"],
                    "pricePerNight": None,
                    "address": f"{city_name} Center",
                    "lat": round(lat + item["dlat"], 5),
                    "lon": round(lon + item["dlon"], 5),
                })
    return hotels[:6]


def fetch_osm_restaurants(destination: str, city_name: str, lat: float, lon: float) -> list:
    """Fetch restaurant and dining suggestions."""
    restaurants = []
    raw_places = search_nominatim_places(f"restaurants in {destination}", limit=6)
    for p in raw_places:
        restaurants.append({
            "name": p["name"],
            "cuisine": "Local & Multi-Cuisine",
            "priceRange": "₹₹",
            "rating": "4.4★",
            "address": p.get("address", destination),
            "lat": p["point"]["lat"],
            "lon": p["point"]["lon"],
        })

    # Ensure at least 4 restaurants exist
    if len(restaurants) < 4:
        contextual = [
            {"name": f"{city_name} Culinary Heritage Bistro", "cuisine": "Local Specialties", "rating": "4.6★", "dlat": 0.005, "dlon": 0.004},
            {"name": f"The Spice Garden Table - {city_name}", "cuisine": "Authentic Regional", "rating": "4.5★", "dlat": -0.006, "dlon": 0.005},
            {"name": f"Old Quarter Cafe & Roastery", "cuisine": "Cafe & Bakery", "rating": "4.4★", "dlat": 0.008, "dlon": -0.005},
            {"name": f"Panorama Sky Lounge & Grill", "cuisine": "Fine Dining", "rating": "4.7★", "dlat": -0.007, "dlon": -0.006},
        ]
        for item in contextual:
            if not any(r["name"].lower() == item["name"].lower() for r in restaurants):
                restaurants.append({
                    "name": item["name"],
                    "cuisine": item["cuisine"],
                    "priceRange": "₹₹",
                    "rating": item["rating"],
                    "address": f"{city_name} Downtown",
                    "lat": round(lat + item["dlat"], 5),
                    "lon": round(lon + item["dlon"], 5),
                })
    return restaurants[:6]


# ════════════════════════════════════════════════════════════════
# HTTP ROUTES
# ════════════════════════════════════════════════════════════════

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


@app.route("/")
@app.route("/api")
@app.route("/api/index")
def index():
    """Serve the frontend index.html."""
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/search-destinations", methods=["GET"])
def destination_search():
    """Destination autocomplete endpoint."""
    query = (request.args.get("q") or "").strip()
    if not query:
        return jsonify({"results": []})
    return jsonify({"results": search_destinations(query, limit=6)})


@app.route("/plan-trip", methods=["POST"])
def plan_trip():
    """Generate spatially clustered, weather-aware itinerary, budget intelligence, and map places."""
    body = request.json or {}
    destination = body.get("destination", "").strip()
    start_date = body.get("startDate") or datetime.now().strftime("%Y-%m-%d")
    num_days = max(1, int(body.get("numDays", 3)))
    budget = int(body.get("budget", 0))
    travel_style = (body.get("travelStyle") or "solo").strip().lower()
    if travel_style not in STYLE_MULTIPLIERS:
        travel_style = "solo"
    pace = (body.get("pace") or "balanced").strip().lower()
    if pace not in ("relaxed", "balanced", "packed"):
        pace = "balanced"

    stops_per_day = {"relaxed": 2, "balanced": 3, "packed": 4}[pace]

    if not destination:
        return jsonify({"error": "destination is required"}), 400

    # 1. Geocode Destination
    destination_matches = search_destinations(destination, limit=1)
    if not destination_matches:
        return jsonify({"error": f"Could not find '{destination}'. Try a more specific name."}), 400

    dest_meta = destination_matches[0]
    lat = dest_meta["lat"]
    lon = dest_meta["lon"]

    # 2. Country Profile & Dynamic Cost-of-Living Budget Intelligence
    country_profile = fetch_country_profile(
        dest_meta.get("country", ""),
        dest_meta.get("country_code", "")
    )
    budget_eval = evaluate_budget_intelligence(
        budget, num_days, dest_meta.get("country_code", ""), travel_style
    )
    budget_breakdown = budget_eval["breakdown"]
    budget_intelligence = budget_eval["intelligence"]
    currency = fetch_currency_conversion(budget, country_profile.get("currencyCode"))

    # 3. Weather Forecast (Open-Meteo)
    weather = fetch_weather(lat, lon, start_date, num_days)
    daily_weather = weather.pop("_daily", [])

    # 4. Discover Attractions (including reserve pool for activity swaps)
    attractions = fetch_attractions(lat, lon, num_days, destination=destination, stops_per_day=stops_per_day)

    # 5. Build Clustered, Weather-Aware Multi-Day Itinerary
    itinerary, unused_attractions = build_itinerary(
        attractions,
        num_days,
        start_date,
        daily_weather,
        origin_lat=lat,
        origin_lon=lon,
        destination=destination,
        country_name=dest_meta.get("country", ""),
        travel_style=travel_style,
        pace=pace,
    )
    itinerary, ai_powered, model_engine = enhance_itinerary_with_ai(
        itinerary, destination, travel_style, pace, budget_intelligence
    )
    itinerary = enrich_itinerary_with_routes(itinerary, lat, lon)

    return jsonify({
        "weather": weather,
        "itinerary": itinerary,
        "unusedAttractions": unused_attractions,
        "budgetBreakdown": budget_breakdown,
        "budgetIntelligence": budget_intelligence,
        "attractions": serialize_attractions(attractions),
        "currency": currency,
        "destinationMeta": dest_meta,
        "countryInsights": country_profile,
        "coordinates": {"lat": lat, "lon": lon},
        "modelMeta": {
            "engine": model_engine,
            "aiPowered": ai_powered,
            "travelStyle": travel_style,
            "pace": pace,
        },
    })


@app.route("/suggestions", methods=["POST"])
def suggestions():
    """Return nearby hotels and restaurants for the chosen destination."""
    body = request.json or {}
    destination = body.get("destination", "").strip()

    if not destination:
        return jsonify({"error": "destination is required"}), 400

    dest_matches = search_destinations(destination, limit=1)
    if not dest_matches:
        return jsonify({"error": f"Could not find '{destination}'"}), 400

    dest_meta = dest_matches[0]
    lat = dest_meta["lat"]
    lon = dest_meta["lon"]
    city_name = dest_meta.get("city") or dest_meta.get("state") or destination.title()

    hotels = fetch_osm_hotels(destination, city_name, lat, lon)
    restaurants = fetch_osm_restaurants(destination, city_name, lat, lon)

    return jsonify({"hotels": hotels, "restaurants": restaurants})


@app.route("/<path:path>")
def static_proxy(path):
    """Serve static assets (style.css, app-enhanced.js, etc.)."""
    file_path = os.path.join(BASE_DIR, path)
    if os.path.exists(file_path):
        return send_from_directory(BASE_DIR, path)
    return jsonify({"error": "Resource not found"}), 404


# ════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n* Planora Travel Planner Server Starting on port {port}...")
    print(f"* Access the web app at: http://localhost:{port}\n")
    app.run(debug=True, host="0.0.0.0", port=port)
