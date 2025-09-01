# -*- coding: utf-8 -*-
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <https://www.gnu.org/licenses/>.

"""
Fetch utilities for BDNS API
Provides concurrent paginated and non-paginated data fetching with generator interface.
"""

import sys
import json
import asyncio
import logging
from typing import Any, Dict, Generator
from concurrent.futures import ThreadPoolExecutor

import aiohttp
from tqdm.asyncio import tqdm
from tenacity import retry, stop_after_attempt, retry_if_exception_type, wait_fixed

from bdns.fetch.utils import format_url


logging.basicConfig(level=logging.WARNING, stream=sys.stderr)
logger = logging.getLogger(__name__)

MAX_RETRIES = 3
"""Maximum number of retries for API requests."""

WAIT_TIME = 2
"""Time to wait between retries in seconds."""


def log_retry_attempt(retry_state):
    # Exception instance from last attempt
    exc = retry_state.outcome.exception()
    exc_type = type(exc).__name__ if exc else "None"
    exc_msg = str(exc) if exc else "No exception"

    logger.warning(
        f' Retrying due to {exc_type}: "{exc_msg}". '
        f"Attempt {retry_state.attempt_number} of {MAX_RETRIES}."
    )


@retry(
    stop=stop_after_attempt(MAX_RETRIES),
    retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
    wait=wait_fixed(WAIT_TIME),
    before_sleep=log_retry_attempt,
)
async def async_fetch_page(semaphore, session, url):
    """
    Fetches data from a single page with error handling and retries.
    Args:
        semaphore (asyncio.Semaphore): The semaphore to control concurrent requests.
        session (aiohttp.ClientSession): The session to use for making requests.
        url (str): The URL to fetch data from.
    Returns:
        dict: The API response containing page data and metadata.
    """
    async with semaphore:
        # Log the outgoing request
        logger.debug(f"HTTP REQUEST: GET {url}")

        start_time = asyncio.get_event_loop().time()
        async with session.get(url) as resp:
            end_time = asyncio.get_event_loop().time()
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds

            # Log response details
            logger.debug(
                f"HTTP RESPONSE: {resp.status} {resp.reason} - {response_time:.1f}ms"
            )
            logger.debug(f"Response Headers: {dict(resp.headers)}")

            data = await resp.json()

            # Log response content size and basic info
            content_size = len(await resp.text()) if hasattr(resp, "text") else 0
            logger.debug(f"Response Content-Length: {content_size} bytes")

            if isinstance(data, dict):
                if "content" in data and isinstance(data["content"], list):
                    logger.debug(f"Response contains {len(data['content'])} items")
                if "totalPages" in data:
                    logger.debug(f"Total pages available: {data['totalPages']}")
                if "number" in data:
                    logger.debug(f"Current page: {data['number']}")

            # Handle API errors
            if "codigo" in data and "error" in data:
                logger.error(f"API Error Response: {data}")
                from bdns.fetch.exceptions import BDNSError

                tech_details = (
                    f"API error code {data['codigo']}: {data['error']} from {url}"
                )
                tech_details += f"\nResponse status: {resp.status}"
                tech_details += f"\nResponse headers: {dict(resp.headers)}"
                tech_details += f"\nFull response data: {data}"

                raise BDNSError(
                    message=f"API returned error: {data['error']}",
                    suggestion="Check your parameters and try again. Use --help for valid options.",
                    technical_details=tech_details,
                )

            if resp.status != 200:
                logger.error(f"HTTP Error {resp.status}: {resp.reason}")
                logger.error(f"Response body: {data}")
                from bdns.fetch.exceptions import handle_api_error

                response_text = (
                    json.dumps(data) if isinstance(data, dict) else str(data)
                )
                raise handle_api_error(
                    resp.status, url, response_text, dict(resp.headers)
                )

            return data


async def async_fetch_paginated_generator(
    base_url: str,
    params: Dict[str, Any],
    from_page: int = 0,
    num_pages: int = 0,
    max_concurrent_requests: int = 5,
):
    """
    Async generator that fetches paginated data with concurrent requests.
    Args:
        base_url (str): The base API endpoint URL.
        params (Dict[str, Any]): Query parameters (without page parameter).
        from_page (int): The page number to start fetching from. Default is 0.
        num_pages (int): The number of pages to fetch. If 0, fetches all pages.
        max_concurrent_requests (int): The maximum number of concurrent requests.
    Yields:
        Dict[str, Any]: Individual items from the API response across all pages.
    """
    semaphore = asyncio.Semaphore(max_concurrent_requests)

    async with aiohttp.ClientSession() as session:
        # Fetch the first page to get total page count
        first_page_params = {**params, "page": from_page}
        first_page_url = format_url(base_url, first_page_params)

        try:
            first_response = await async_fetch_page(semaphore, session, first_page_url)
            total_pages = first_response.get("totalPages", 1)

            # Yield items from the first page
            content = first_response.get("content", [])
            if isinstance(content, list):
                for item in content:
                    yield item

            # Determine pages to fetch
            to_page = (
                total_pages
                if num_pages == 0
                else min(from_page + num_pages, total_pages)
            )

            # If there are more pages, fetch them concurrently
            if from_page + 1 < to_page:
                # Create tasks for remaining pages
                tasks = []
                for page in range(from_page + 1, to_page):
                    page_params = {**params, "page": page}
                    page_url = format_url(base_url, page_params)
                    tasks.append(
                        asyncio.create_task(
                            async_fetch_page(semaphore, session, page_url)
                        )
                    )

                # Process completed tasks as they finish
                for task in tqdm(
                    asyncio.as_completed(tasks),
                    total=len(tasks),
                    desc="Fetching pages",
                ):
                    try:
                        response = await task
                        content = response.get("content", [])
                        if isinstance(content, list):
                            for item in content:
                                yield item
                    except Exception as e:
                        logger.error(f"Error fetching page: {e}")
                        continue

        except Exception as e:
            logger.error(f"Error in paginated fetch: {e}")
            raise


def fetch_paginated(
    base_url: str,
    params: Dict[str, Any],
    from_page: int = 0,
    num_pages: int = 0,
    max_concurrent_requests: int = 5,
) -> Generator[Dict[str, Any], None, None]:
    """
    Synchronous generator wrapper for paginated data fetching.

    This function provides a clean synchronous interface over the async pagination logic,
    making it easy to use in synchronous code contexts like the BDNSClient.

    Args:
        base_url (str): The base API endpoint URL.
        params (Dict[str, Any]): Query parameters (without page parameter).
        from_page (int): The page number to start fetching from. Default is 0.
        num_pages (int): The number of pages to fetch. If 0, fetches all pages.
        max_concurrent_requests (int): The maximum number of concurrent requests.

    Yields:
        Dict[str, Any]: Individual items from the API response across all pages.

    Example:
        # Fetch all pages
        for item in fetch_paginated("https://api.example.com/search", {"query": "test"}):
            print(item)

        # Fetch first 3 pages only
        for item in fetch_paginated("https://api.example.com/search", {"query": "test"}, num_pages=3):
            print(item)
    """

    # Run the async generator in a new event loop
    def run_async_generator():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            async_gen = async_fetch_paginated_generator(
                base_url, params, from_page, num_pages, max_concurrent_requests
            )

            async def collect_items():
                items = []
                async for item in async_gen:
                    items.append(item)
                return items

            return loop.run_until_complete(collect_items())
        finally:
            loop.close()

    # Use ThreadPoolExecutor to avoid blocking the main thread
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(run_async_generator)
        items = future.result()

    # Yield each item
    for item in items:
        yield item


@retry(
    stop=stop_after_attempt(MAX_RETRIES),
    retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
    wait=wait_fixed(WAIT_TIME),
    before_sleep=log_retry_attempt,
)
async def async_fetch_single(session, url):
    """
    Fetches data from a single URL with error handling and retries.
    Args:
        session (aiohttp.ClientSession): The session to use for making requests.
        url (str): The URL to fetch data from.
    Returns:
        Any: The API response data.
    """
    # Log the outgoing request
    logger.debug(f"HTTP REQUEST: GET {url}")

    start_time = asyncio.get_event_loop().time()
    async with session.get(url) as resp:
        end_time = asyncio.get_event_loop().time()
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds

        # Log response details
        logger.debug(
            f"HTTP RESPONSE: {resp.status} {resp.reason} - {response_time:.1f}ms"
        )
        logger.debug(f"Response Headers: {dict(resp.headers)}")

        data = await resp.json()

        # Log response content size and basic info
        content_size = len(await resp.text()) if hasattr(resp, "text") else 0
        logger.debug(f"Response Content-Length: {content_size} bytes")

        if isinstance(data, dict):
            if "content" in data and isinstance(data["content"], list):
                logger.debug(f"Response contains {len(data['content'])} items")
        elif isinstance(data, list):
            logger.debug(f"Response contains {len(data)} items")

        # Handle API errors
        if isinstance(data, dict) and "codigo" in data and "error" in data:
            logger.error(f"API Error Response: {data}")
            from bdns.fetch.exceptions import BDNSAPIError

            tech_details = (
                f"API error code {data['codigo']}: {data['error']} from {url}"
            )
            tech_details += f"\nResponse status: {resp.status}"
            tech_details += f"\nResponse headers: {dict(resp.headers)}"
            tech_details += f"\nFull response data: {data}"

            raise BDNSAPIError(
                message=f"API returned error: {data['error']}",
                suggestion="Check your parameters and try again. Use --help for valid options.",
                technical_details=tech_details,
            )

        if resp.status != 200:
            logger.error(f"HTTP Error {resp.status}: {resp.reason}")
            logger.error(f"Response body: {data}")
            from bdns.fetch.exceptions import handle_api_error

            response_text = json.dumps(data) if isinstance(data, dict) else str(data)
            raise handle_api_error(resp.status, url, response_text, dict(resp.headers))

        return data


def fetch(
    url: str, params: Dict[str, Any] = None
) -> Generator[Dict[str, Any], None, None]:
    """
    Fetches data from a single non-paginated endpoint with retries and error handling.

    This function provides a clean synchronous interface for fetching data from BDNS API
    endpoints that don't use pagination (like reference data, documents, etc.).

    This is an improved version of utils.api_request() with the following enhancements:
    - Retry logic with exponential backoff (3 attempts, 2-second wait)
    - Proper async HTTP handling with aiohttp (more robust than requests)
    - Comprehensive error handling for API errors, HTTP errors, and network issues
    - Support for different response formats (lists, paginated content, single objects)
    - Detailed logging and debugging information
    - Generator interface for consistent API with fetch_paginated()

    Args:
        url (str): The API endpoint URL.
        params (Dict[str, Any], optional): Query parameters for the request.

    Yields:
        Dict[str, Any]: Individual items from the API response.

    Example:
        # Fetch actividades data
        for item in fetch("https://api.example.com/actividades", {"vpd": "GE"}):
            print(item)

        # Fetch a specific document
        for item in fetch("https://api.example.com/documents/123"):
            print(item)
    """
    # Format URL with parameters
    if params:
        full_url = format_url(url, params)
    else:
        full_url = url

    # Run the async fetch in a new event loop
    def run_async_fetch():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:

            async def fetch_data():
                async with aiohttp.ClientSession() as session:
                    return await async_fetch_single(session, full_url)

            return loop.run_until_complete(fetch_data())
        finally:
            loop.close()

    # Use ThreadPoolExecutor to avoid blocking the main thread
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(run_async_fetch)
        data = future.result()

    # Yield individual items based on response structure
    if isinstance(data, list):
        # Direct list response
        for item in data:
            yield item
    elif isinstance(data, dict):
        if "content" in data and isinstance(data["content"], list):
            # Paginated response structure (but single page)
            for item in data["content"]:
                yield item
        else:
            # Single object response
            yield data
    else:
        logger.warning(f"Unexpected response type: {type(data)}")
        yield data


def fetch_binary(url: str) -> bytes:
    """
    Synchronously fetches binary content from a URL using requests.
    Simple and straightforward - no async complexity needed.

    Args:
        url: The URL to fetch binary content from.

    Returns:
        bytes: The binary content response.

    Raises:
        requests.RequestException: If the request fails.
    """
    import requests
    from bdns.fetch.exceptions import handle_api_response

    logger.debug(f"Starting binary fetch from: {url}")

    try:
        response = requests.get(url, timeout=30)

        logger.debug(
            f"Binary response: {response.status_code} - Content-Type: {response.headers.get('content-type', 'unknown')}"
        )

        if response.status_code == 200:
            content = response.content
            logger.debug(f"Binary content fetched: {len(content)} bytes")
            return content
        elif response.status_code == 204:
            logger.debug("No content returned (204)")
            return b""
        elif response.status_code == 404:
            logger.warning(f"Resource not found (404) for URL: {url}")
            return b""
        else:
            # Handle API errors using existing error handler
            raise handle_api_response(
                response.status_code, url, response.text, dict(response.headers)
            )
    except requests.RequestException as e:
        logger.error(f"Request failed for binary fetch: {e}")
        raise
