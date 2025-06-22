import json
import os

import requests
import time
import random
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    retry_if_result,
)


def is_rate_limited(response):
    """Check if the response indicates rate limiting (status code 429)"""
    return response.status_code == 429


@retry(
    retry=(retry_if_result(is_rate_limited)),
    wait=wait_exponential(multiplier=1, min=4, max=60),
    stop=stop_after_attempt(5),
)
def make_request(url, headers):
    """Make a request with retry logic for rate limiting"""
    # Random delay before each request to avoid detection
    time.sleep(random.uniform(2, 6))
    response = requests.get(url, headers=headers)
    return response


def get_trading212_data(query, ticker=None, next_page_path=None):
    """
    Fetch personal Trading212 data for a given query.
    query: str - search query
    start_date: str - start date in the format yyyy-mm-dd or mm/dd/yyyy
    end_date: str - end date in the format yyyy-mm-dd or mm/dd/yyyy
    """
    api_key = os.getenv('TRADING_212_API_KEY')
    if not api_key:
        raise ValueError("TRADING_212_API_KEY environment variable not set")

    url = ""
    if query == "positions":
        url = f"https://demo.trading212.com/api/v0/equity/portfolio"
    elif query == "position":
        url = f"https://demo.trading212.com/api/v0/equity/portfolio/{ticker}"
    elif query == "account balance":
        url = f"https://demo.trading212.com/api/v0/equity/account/cash"
    elif query == "transaction history":
        if next_page_path is None:
            url = f"https://demo.trading212.com/api/v0/history/transactions"
        else:
            url = next_page_path
    else:
        raise ValueError(f"Input '{query}' is not a valid query.")

    headers = {"Authorization": api_key}

    trading212_result = ""
    try:
        response = make_request(url, headers)
        trading212_result = response

    except Exception as e:
        print(f"Failed after multiple retries: {e}")

    return trading212_result.json()
