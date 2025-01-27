import requests

def get_weather_data(latitude, longitude):
    """
    Fetches weather data from the Open-Meteo API.

    Args:
        latitude (float): Latitude of the location.
        longitude (float): Longitude of the location.

    Returns:
        dict: Parsed JSON response containing weather data.
    """
    base_url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,wind_speed_10m,precipitation",
        "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation",
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise HTTPError for bad responses
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data: {e}")
        return None

# Example usage
if __name__ == "__main__":
    # Coordinates for Rio de Janeiro, Brazil
    latitude = -22.9068
    longitude = -43.1729

    weather_data = get_weather_data(latitude, longitude)
    if weather_data:
        print(weather_data)