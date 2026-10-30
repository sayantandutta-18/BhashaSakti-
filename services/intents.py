"""
Intent handlers for time, weather (Open-Meteo), and grounded FAQ lookup.
Zero API keys required for tool execution.
"""

import os
import json
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional, Dict, Any
import requests

logger = logging.getLogger(__name__)

# Haldia, West Bengal coordinates as default
DEFAULT_CITY = "Haldia"
DEFAULT_LAT = 22.0645
DEFAULT_LON = 88.0772

WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snowfall",
    73: "Moderate snowfall",
    75: "Heavy snowfall",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm"
}

def get_current_time(lang: str = "hi") -> str:
    """Return formatted current time and date in Asia/Kolkata timezone."""
    kolkata_tz = ZoneInfo("Asia/Kolkata")
    now = datetime.now(kolkata_tz)
    time_str = now.strftime("%I:%M %p")
    date_str = now.strftime("%A, %d %B %Y")
    return f"Time: {time_str}, Date: {date_str} (Asia/Kolkata IST)"

def get_weather(city: Optional[str] = None, lang: str = "hi") -> str:
    """
    Fetch current weather using Open-Meteo free APIs (no key needed).
    Defaults to Haldia if no city is identified.
    """
    target_city = city.strip() if city and city.strip() else DEFAULT_CITY
    lat, lon = DEFAULT_LAT, DEFAULT_LON

    # Attempt geocoding if a specific non-Haldia city is requested
    if target_city.lower() != "haldia":
        try:
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={target_city}&count=1&language=en&format=json"
            res = requests.get(geo_url, timeout=5)
            if res.status_code == 200:
                data = res.json()
                if "results" in data and len(data["results"]) > 0:
                    first = data["results"][0]
                    lat = first.get("latitude", lat)
                    lon = first.get("longitude", lon)
                    target_city = first.get("name", target_city)
        except Exception as e:
            logger.warning(f"Geocoding error for city '{city}', falling back to default: {e}")

    # Query Open-Meteo forecast endpoint
    try:
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m"
        )
        res = requests.get(weather_url, timeout=5)
        if res.status_code == 200:
            data = res.json().get("current", {})
            temp = data.get("temperature_2m", "N/A")
            humidity = data.get("relative_humidity_2m", "N/A")
            wind = data.get("wind_speed_10m", "N/A")
            code = data.get("weather_code", 0)
            desc = WEATHER_CODES.get(code, "Clear/Fair")
            return f"Location: {target_city}. Temperature: {temp}°C, Condition: {desc}, Humidity: {humidity}%, Wind: {wind} km/h."
    except Exception as e:
        logger.error(f"Weather lookup failed: {e}")

    return f"Location: {target_city}. Weather data temporarily unavailable."

def get_faq_answer(query: str, lang: str = "hi") -> Optional[str]:
    """Retrieve grounded answer from faq.json based on keyword matching."""
    faq_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "faq.json")
    if not os.path.exists(faq_path):
        return None

    try:
        with open(faq_path, "r", encoding="utf-8") as f:
            faq_data = json.load(f)

        query_lower = query.lower()
        best_match = None
        max_overlap = 0

        for item in faq_data:
            keywords = item.get("keywords", [])
            overlap = sum(1 for kw in keywords if kw.lower() in query_lower)
            if overlap > max_overlap:
                max_overlap = overlap
                best_match = item

        if best_match and max_overlap > 0:
            answers = best_match.get("answer", {})
            return answers.get(lang, answers.get("en", ""))
    except Exception as e:
        logger.error(f"Error reading faq.json: {e}")

    return None

def execute_intent(intent: str, query: str, city: Optional[str] = None, lang: str = "hi") -> Optional[str]:
    """
    Execute tool based on detected intent: 'time', 'weather', or 'faq'.
    Returns raw data string for Gemma to phrase naturally into the target language.
    """
    if intent == "time":
        return get_current_time(lang)
    elif intent == "weather":
        return get_weather(city, lang)
    elif intent == "faq":
        faq_res = get_faq_answer(query, lang)
        if faq_res:
            return f"FAQ Knowledge Base Fact: {faq_res}"
    return None
