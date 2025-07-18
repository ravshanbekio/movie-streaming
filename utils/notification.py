import requests
from typing import List

FIREBASE_API_KEY = "YOUR_FIREBASE_SERVER_KEY"
FCM_URL = "https://fcm.googleapis.com/fcm/send"

def chunk_list(data: List[str], chunk_size: int = 500):
    """Yield successive chunks of 500 tokens."""
    for i in range(0, len(data), chunk_size):
        yield data[i:i + chunk_size]

def send_push_batch(tokens: List[str], title: str, body: str):
    headers = {
        "Authorization": f"key={FIREBASE_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "registration_ids": tokens,
        "notification": {
            "title": title,
            "body": body
        }
    }

    response = requests.post(FCM_URL, json=payload, headers=headers)
    return response.json()

def send_to_all_users(all_tokens: List[str], title: str, body: str):
    results = []
    for batch in chunk_list(all_tokens, 500):
        result = send_push_batch(batch, title, body)
        results.append(result)
    return results
