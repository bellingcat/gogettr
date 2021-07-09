"""Defines the ApiClient class, which provides a standard interface for interacting with
the GETTR API."""

import itertools
import logging
import time
from typing import Callable, Iterator

import requests
from requests.exceptions import ReadTimeout

from gogettr.errors import GettrApiError


class ApiClient:
    """A standard and safe way to interact with the GETTR API. Catches errors, supports
    retries, etc."""

    def __init__(self, api_base_url: str = None):
        """Initializes the API client. Optionally takes in a base URL for the GETTR api."""
        self.api_base_url = api_base_url or "https://api.gettr.com"

    def get(
        self, url: str, params: dict = None, retries: int = 3, key: str = "result"
    ) -> dict:
        """Makes a request to the given API endpoint and returns the 'results' object.
        Supports retries. Soon will support authentication."""
        tries = 0
        error = None

        def handle_error(issue):
            global error
            logging.warning(
                "Unable to pull from API: %s. Waiting %s seconds before retrying (%s/%s)...",
                issue,
                4 ** tries,
                tries,
                retries,
            )
            time.sleep(4 ** tries)
            error = issue

        while tries < retries:
            logging.info("Requesting %s (params: %s)...", url, params)
            tries += 1

            try:
                resp = requests.get(self.api_base_url + url, params=params, timeout=10)
            except ReadTimeout as e:
                handle_error({"timeout": e})
                continue

            logging.info("%s gave response: %s", url, resp.text)

            if resp.status_code in [429, 500, 502, 503, 504]:
                handle_error({"status_code": resp.status_code})
                continue

            logging.debug("GET %s with params %s yielded %s", url, params, resp.content)

            data = resp.json()
            if key in data:
                return data[key]
            if "error" in data:
                error = data["error"]

        raise GettrApiError(error)

    def get_paginated(
        self,
        *args,
        offset_param: str = "offset",
        offset_start: int = 0,
        offset_step: int = 20,
        result_count_func: Callable[[dict], int] = lambda k: len(k["data"]["list"]),
        **kwargs
    ) -> Iterator[dict]:
        """Paginates requests to the given API endpoint."""
        for i in itertools.count(start=offset_start, step=offset_step):
            params = kwargs.get("params", {})
            params[offset_param] = i
            kwargs["params"] = params
            data = self.get(*args, **kwargs)
            yield data

            # End if no more results
            if result_count_func(data) == 0:
                return
