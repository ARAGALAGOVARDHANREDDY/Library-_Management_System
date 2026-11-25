import os
import requests

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")

class APIError(Exception):
    pass

def api_request(method, endpoint, token=None, data=None, params=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        response = requests.request(
            method, f"{API_BASE_URL}{endpoint}", headers=headers,
            json=data, params=params, timeout=20
        )
        if response.status_code >= 400:
            try:
                message = response.json().get("detail", "API request failed")
            except ValueError:
                message = response.text or "API request failed"
            raise APIError(f"Error {response.status_code}: {message}")
        return response.json() if response.content else {}
    except requests.exceptions.ConnectionError as error:
        raise APIError("Cannot connect to the Library API. Check API_BASE_URL and backend status.") from error
    except requests.exceptions.Timeout as error:
        raise APIError("The API request timed out. Please try again.") from error
    except requests.exceptions.RequestException as error:
        raise APIError(str(error)) from error

def login_user(email, password):
    return api_request("POST", "/auth/login", data={"email": email, "password": password})

def register_student(email, password, member_id):
    return api_request("POST", "/auth/register", data={"email": email, "password": password, "role": "student", "member_id": member_id})
