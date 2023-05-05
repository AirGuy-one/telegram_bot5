import requests
import os

from dotenv import load_dotenv


def get_access_token():
    load_dotenv()

    url = "https://useast.api.elasticpath.com/oauth/access_token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "client_credentials",
        "client_id": os.environ.get('CLIENT_ID'),
        "client_secret": os.environ.get('CLIENT_SECRET')
    }

    response = requests.post(url, headers=headers, data=data)
    access_token = response.json()["access_token"]

    return access_token
