"""Defines the PublicClient, which is the primary way to interface with the
unauthenticated GETTR API."""
# pylint: disable=W0622 # we have variables called "max", "all", etc.

import json

from gogettr.api import ApiClient
from gogettr.public import PublicClient

class PrivateClient(PublicClient):
    """A client for all the private GETTR methods. If the API requires an
    account to pull the data, it belongs here."""

    def __init__(self, username: str, token: str):
        headers = {
            'X-App-Auth': json.dumps({
                'user': username.lower(), 
                'token': token
            }),
        }
        self.api_client = ApiClient(headers = headers)