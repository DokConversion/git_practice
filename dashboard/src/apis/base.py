import time
import requests
from abc import ABC, abstractmethod
from datetime import date


class APIError(Exception):
    pass


class APIClient(ABC):
    def __init__(self, client_id: int, credentials: dict[str, str]):
        self.client_id = client_id
        self.credentials = credentials
        self.session = requests.Session()

    @abstractmethod
    def fetch(self, date_from: date, date_to: date) -> dict:
        ...

    def _request(self, method: str, url: str, max_retries: int = 3, **kwargs) -> requests.Response:
        last_exc = None
        for attempt in range(max_retries):
            try:
                resp = self.session.request(method, url, timeout=30, **kwargs)
                if resp.status_code == 429 or resp.status_code >= 500:
                    raise requests.HTTPError(f"HTTP {resp.status_code}", response=resp)
                resp.raise_for_status()
                return resp
            except (requests.RequestException, requests.HTTPError) as exc:
                last_exc = exc
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
        raise APIError(f"Request failed after {max_retries} attempts: {last_exc}")
