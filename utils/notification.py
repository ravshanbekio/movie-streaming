import logging
from typing import List

import firebase_admin
from firebase_admin import credentials, messaging

# Initialize Firebase Admin SDK
cred = credentials.Certificate("firebase.json")  # Ensure this path is correct
firebase_admin.initialize_app(cred)

def chunk_list(data: List[str], chunk_size: int = 500):
    """Yield successive chunks of up to 500 tokens."""
    for i in range(0, len(data), chunk_size):
        yield data[i:i + chunk_size]

def send_push_batch(tokens: List[str], title: str, body: str):
    try:
        message = messaging.MulticastMessage(
            tokens=tokens,
            notification=messaging.Notification(
                title=title,
                body=body
            )
        )

        response = messaging.send_each_for_multicast(message)

        failed = []
        for i, resp in enumerate(response.responses):
            if not resp.success:
                failed.append({
                    "token": tokens[i],
                    "error": str(resp.exception)
                })

        return {
            "success_count": response.success_count,
            "failure_count": response.failure_count,
            "failed": failed
        }

    except Exception as e:
        logging.error(f"Firebase batch send error: {e}")
        return {
            "status": "error",
            "error": str(e)
        }
    except Exception as e:
        logging.error(f"Firebase batch send error: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

def send_to_all_users(all_tokens: List[str], title: str, body: str):
    """Send push notifications to all users in batches of 500."""
    results = []
    for batch in chunk_list(all_tokens, 500):
        result = send_push_batch(batch, title, body)
        results.append(result)
    return results

