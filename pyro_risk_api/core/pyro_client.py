from urllib.parse import urljoin

import requests
from pyroclient import Client

from pyro_risk_api.core.config import settings


def login() -> str:
    resp = requests.post(
        urljoin(settings.pyro_api_host, "api/v1/login/creds"),
        data={"username": settings.pyro_api_username, "password": settings.pyro_api_password},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def build_client() -> Client:
    return Client(token=login(), host=settings.pyro_api_host)
