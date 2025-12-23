import asyncio
import logging
import os
import httpx
import bmasterai
from fastmcp import FastMCP, Context

# Initialize BMasterAI Logging
bmasterai.configure_logging(log_file='weather_mcp.log', json_log_file='weather_mcp.jsonl')
logger = bmasterai.get_logger()

# Configure logging - REMOVED to use BMasterAI
# logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)
# logger = logging.getLogger("weather-mcp")

# Initialize FastMCP server
mcp = FastMCP("Weather MCP Server 🌤️")

@mcp.tool()
async def get_weather_forecast(city: str, days: int = 3) -> dict:
    """
    Get weather forecast for a specific city.

    Args:
        city: The name of the city (e.g., "Indianapolis", "San Francisco").
        days: Number of forecast days (default: 3).

    Returns:
        A dictionary containing weather forecast data.
    """
    logger.logger.info(f"--- 🌤️ Tool: get_weather_forecast called for {city} ({days} days) ---")
    logger.log_event("weather-mcp", bmasterai.EventType.TOOL_USE, f"Fetching weather for {city}", metadata={"city": city, "days": days})

    try:
        # 1. Geocoding
        geo_url = "https://geocoding-api.open-meteo.com/v1/search"
        params = {"name": city, "count": 1, "language": "en", "format": "json"}
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(geo_url, params=params)
            data = resp.json()
            
            if not data.get("results"):
                 return {"error": f"City '{city}' not found."}
                 
            lat = data["results"][0]["latitude"]
            lon = data["results"][0]["longitude"]
            city_name = data["results"][0]["name"]
            country = data["results"][0].get("country", "Unknown")
            
            logger.logger.info(f"Resolved {city} to {lat}, {lon}")

            # Now fetch weather forecast
            weather_response = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "daily": "weather_code,temperature_2m_max,temperature_2m_min",
                    "forecast_days": days,
                    "timezone": "auto",
                },
            )
            weather_response.raise_for_status()
            weather_data = weather_response.json()
            
            daily = weather_data.get("daily", {})
            units = weather_data.get("daily_units", {})
            
            # Helper to convert C to F
            def c_to_f(c_list):
                return [round((t * 9/5) + 32, 1) if t is not None else None for t in c_list]

            # Add F data
            if "temperature_2m_max" in daily:
                daily["temperature_2m_max_f"] = c_to_f(daily["temperature_2m_max"])
                units["temperature_2m_max_f"] = "°F"
                
            if "temperature_2m_min" in daily:
                daily["temperature_2m_min_f"] = c_to_f(daily["temperature_2m_min"])
                units["temperature_2m_min_f"] = "°F"

            return {
                "location": f"{city_name}, {country}",
                "forecast": daily,
                "units": units
            }

    except httpx.HTTPError as e:
        logger.logger.error(f"❌ API request failed: {e}")
        return {"error": f"Failed to fetch weather data: {str(e)}"}
    except Exception as e:
        logger.logger.error(f"❌ Unexpected error: {e}")
        return {"error": f"An unexpected error occurred: {str(e)}"}

if __name__ == "__main__":
    logger.logger.info(f"🚀 Weather MCP server started on port {os.getenv('PORT', 8080)}")
    asyncio.run(
        mcp.run_async(
            transport="http",
            host="0.0.0.0",
            port=int(os.getenv("PORT", 8080)),
        )
    )
