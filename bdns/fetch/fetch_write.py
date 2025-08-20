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
Created on Sat May 17 16:23:45 2025
Author: josemariacruzlorite@gmail.com
"""

import sys
import json
import asyncio
import logging
import requests

import aiohttp
from tqdm.asyncio import tqdm
from tenacity import retry, stop_after_attempt, retry_if_exception_type, wait_fixed

from bdns.fetch.utils import smart_open, api_request


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


def write_to_file(output_stream, item):
    """
    Writes an item to the output stream. If the item is a list, it writes each element in a new line.
    If the item is a dict, it writes the dict as a JSON object in a new line.
    Args:
        output_stream (file-like object): The output stream to write to.
        item (dict or list): The item to write.
    """
    if isinstance(item, list):
        for element in item:
            output_stream.write(json.dumps(element, ensure_ascii=False) + "\n")
    else:
        output_stream.write(json.dumps(item, ensure_ascii=False) + "\n")


@retry(
    wait=wait_fixed(WAIT_TIME),
    stop=stop_after_attempt(MAX_RETRIES),
    retry=retry_if_exception_type((ConnectionError, requests.RequestException)),
    before_sleep=log_retry_attempt,
)
def fetch_and_write(url, output_file):
    """
    Synchronously fetches data from the API endpoint. This is for non-paginated endpoints.
    Args:
        url (str): The URL to fetch data from.
        output_file (str): The file to write the output to.
    """
    response = api_request(url)
    if response:
        with smart_open(output_file, "w", encoding="utf-8", buffering=1) as f:
            write_to_file(f, response)
    else:
        logger.warning(f"Failed to fetch data from {url}. No response received.")


def fetch_and_write_raw(url, output_file):
    """
    Synchronously fetches a document from the API endpoint and writes it to a file.
    This is for non-paginated endpoints where the response is a document (e.g., PDF, DOCX).
    This function does not parse the response as JSON, but writes it directly to the file.
    Args:
        url (str): The URL to fetch the document from.
        output_file (str): The file to write the document to.
    """
    from bdns.fetch.exceptions import handle_api_response

    response = requests.get(url)
    if response.status_code == 200:
        result = response.content
    else:
        raise handle_api_response(
            response.status_code, url, response.text, dict(response.headers)
        )
    if response:
        with smart_open(output_file, "wb") as f:
            f.write(result)
    else:
        logger.warning(f"Failed to fetch document from {url}. No response received.")


@retry(
    wait=wait_fixed(WAIT_TIME),
    stop=stop_after_attempt(MAX_RETRIES),
    retry=retry_if_exception_type((ConnectionError, aiohttp.ClientConnectionError)),
    before_sleep=log_retry_attempt,
)
async def async_fetch_and_enqueue_paginated(semaphore, session, url, queue):
    """
    Fetches data from the API and enqueues results into a queue.
    Args:
        semaphore (asyncio.Semaphore): The semaphore to control concurrent requests.
        session (aiohttp.ClientSession): The session to use for making requests.
        url (str): The URL to fetch data from.
        queue (asyncio.Queue): The queue to enqueue results into.
    Returns:
        tuple: A tuple containing the two values:
            - is_last (bool): True if this is the last page, False otherwise.
            - total_pages (int): The total number of pages available.
    """
    logger = logging.getLogger(__name__)

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
                import json
                from bdns.fetch.exceptions import handle_api_error

                response_text = (
                    json.dumps(data) if isinstance(data, dict) else str(data)
                )
                raise handle_api_error(
                    resp.status, url, response_text, dict(resp.headers)
                )

            await queue.put(data["content"])
            return data.get("number", None), data.get("totalPages")


async def async_writer(queue, output_file):
    """
    Asynchronously writes items from the queue to a file. When it encounters a None item, it stops writing.
    Args:
        queue (asyncio.Queue): The queue containing items to write.
        output_file (str): The file to write the output to.
    """
    try:
        with smart_open(output_file, "w", encoding="utf-8", buffering=1) as f:
            while True:
                item = await queue.get()
                if item is None:
                    break
                write_to_file(f, item)
    except FileNotFoundError:
        print(
            f"Error: The file {output_file} could not be opened for writing.",
            file=sys.stderr,
        )
    except Exception as e:
        print(
            f"Error: An unexpected error occurred while writing to {output_file}: {e}",
            file=sys.stderr,
        )


async def fetch_and_write_paginated(
    url, output_file, from_page=0, num_pages=1, max_concurrent_requests=5
):
    """
    Fetches data from the API and writes it to a file asynchronously.
    Args:
        url (str): The starting URL to fetch data from. This must not include page query parameter.
        output_file (str): The file to write the output to.
        from_page (int): The page number to start fetching from. Default is 0.
        num_pages (int): The number of pages to fetch. If 0 or None, fetches all pages.
        max_concurrent_requests (int): The maximum number of concurrent requests. Default is 5.
    """
    semaphore = asyncio.Semaphore(max_concurrent_requests)
    queue = asyncio.Queue()
    async with aiohttp.ClientSession() as session:
        writer_task = asyncio.create_task(async_writer(queue, output_file))

        # fetch the first page to find out if there are more pages
        page = from_page
        url_with_page = f"{url}&page={page}"
        number, total_pages = await async_fetch_and_enqueue_paginated(
            semaphore, session, url_with_page, queue
        )
        page += 1
        to_page = (
            total_pages if num_pages == 0 else min(from_page + num_pages, total_pages)
        )

        # generate task for subsequent pages if not the last page
        tasks = []
        for page in range(page, to_page):
            url_with_page = f"{url}&page={page}"
            tasks.append(
                asyncio.create_task(
                    async_fetch_and_enqueue_paginated(
                        semaphore, session, url_with_page, queue
                    )
                )
            )

        for task in tqdm(
            asyncio.as_completed(tasks),
            initial=1,
            total=len(tasks) + 1,
            desc="Fetching pages",
        ):
            await task

        await queue.put(None)
        await writer_task
