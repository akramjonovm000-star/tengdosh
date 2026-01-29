import requests

def test_login():
    url = "http://localhost:8000/api/v1/auth/hemis"
    # Sending dummy creds to check connectivity
    data = {"login": "123", "password": "123"}
    try:
        resp = requests.post(url, json=data)
        print(f"Status: {resp.status_code}")
        print(f"Body: {resp.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_login()
