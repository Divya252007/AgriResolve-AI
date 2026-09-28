
import os
import uuid
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("PLANT_HEALTH_API_KEY")

API_URL = "https://planthealthengine.com/api/v1/diagnose"


def analyze_plant(image_bytes, crop):

    if not API_KEY:
        return {
            "success": False,
            "unsupported_crop": False,
            "error": "PLANT_HEALTH_API_KEY is missing."
        }

    try:
        files = {
            "image": (
                "plant.jpg",
                image_bytes,
                "image/jpeg"
            )
        }

        data = {
            "crop": str(crop).strip().lower()
        }

        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Idempotency-Key": str(uuid.uuid4())
        }

        response = requests.post(
            API_URL,
            headers=headers,
            files=files,
            data=data,
            timeout=30
        )

        # Successful diagnosis
        if response.status_code == 200:
            return {
                "success": True,
                "unsupported_crop": False,
                "data": response.json()
            }

        # API does not support the selected crop
        if response.status_code == 400:
            return {
                "success": False,
                "unsupported_crop": True,
                "error": (
                    f"Plant image analysis is not currently "
                    f"supported for '{crop}'."
                )
            }

        # Other API error
        return {
            "success": False,
            "unsupported_crop": False,
            "error": (
                f"API Error {response.status_code}: "
                f"{response.text}"
            )
        }

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "unsupported_crop": False,
            "error": "Plant health API request timed out."
        }

    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "unsupported_crop": False,
            "error": f"Network error: {str(e)}"
        }

    except Exception as e:
        return {
            "success": False,
            "unsupported_crop": False,
            "error": f"Unexpected error: {str(e)}"
        }