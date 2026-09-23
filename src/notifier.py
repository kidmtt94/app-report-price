import logging
from typing import Optional
import requests

logger = logging.getLogger(__name__)


class BarkNotifier:
    def __init__(self, bark_key: Optional[str], server_url: str = "https://api.day.app"):
        self.bark_key = bark_key
        self.server_url = server_url.rstrip("/")

    def send(
        self,
        title: str,
        body: str,
        group: str = "ChungKhoan",
        sound: str = "minuet",
        icon: Optional[str] = None,
        is_dry_run: bool = False,
    ) -> bool:
        """
        Sends a push notification to Bark on iOS.
        """
        if is_dry_run:
            print("\n[DRY RUN] Would send Bark notification:")
            print(f"Title: {title}")
            print(f"Body:\n{body}")
            print("-" * 50)
            return True

        if not self.bark_key:
            logger.warning("Bark key is not provided. Skipping push notification.")
            print("[WARN] No Bark Key provided. Skipping iOS notification.")
            return False

        endpoint = f"{self.server_url}/{self.bark_key}"
        payload = {
            "title": title,
            "body": body,
            "group": group,
            "sound": sound,
        }
        if icon:
            payload["icon"] = icon

        try:
            response = requests.post(endpoint, json=payload, timeout=10)
            if response.status_code == 200:
                res_data = response.json()
                if res_data.get("code") == 200:
                    print(f"[SUCCESS] Push notification sent to Bark successfully.")
                    return True
                else:
                    print(f"[ERROR] Bark responded with message: {res_data.get('message')}")
                    return False
            else:
                print(f"[ERROR] Bark request failed: HTTP {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"[ERROR] Failed to send notification via Bark: {e}")
            return False

