import requests


API_URL = "https://api.open-meteo.com/v1/forecast"


def get_weather(latitude, longitude):

    params = {
        "latitude": latitude,
        "longitude": longitude,

        "current": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "precipitation,"
            "rain,"
            "wind_speed_10m"
        ),

        "daily": (
            "precipitation_probability_max,"
            "precipitation_sum,"
            "temperature_2m_max,"
            "temperature_2m_min"
        ),

        "forecast_days": 7,

        "timezone": "auto"
    }

    try:

        response = requests.get(
            API_URL,
            params=params,
            timeout=15
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.Timeout:

        raise Exception(
            "Weather service timed out. Please try again."
        )

    except requests.exceptions.ConnectionError:

        raise Exception(
            "Unable to connect to the weather service. "
            "Please check your internet connection."
        )

    except requests.exceptions.RequestException as e:

        raise Exception(
            f"Weather service error: {str(e)}"
        )