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
from contextlib import contextmanager
from datetime import datetime
import requests



def format_date_for_api_request(date: datetime, output_format: str = "%d/%m/%Y"):
    """
    Formats a date for API requests.
    Args:
        date (datetime): The date to format.
        output_format (str): The format to use for the date. Default is "%d/%m/%Y".
    Returns:
        str: The formatted date as a string.
    """
    if date is None:
        return None
    if not isinstance(date, datetime):
        raise ValueError("The date must be a datetime object.")
    return date.strftime(output_format)


def format_url(
        url: str,
        query_params: dict):
    """
    Formats a URL with query parameters.
    Args:
        url (str): The base URL.
        query_params (dict): A dictionary containing the query parameters.
    Returns:
        str: The formatted URL with query parameters.
    """
    if not url.endswith("?"):
        url += "?"
    url += "&".join([f"{key}={value}" for key, value in query_params.items() if value is not None])
    return url


def api_request(url):
    """
    Fetches data from the BDNS API for concessions for a given date.
    Args:
        url (str): The URL to fetch data from.
    Returns:
        dict: A dictionary containing concessions data.
    Raises:
        Exception: If the API request fails.
    """
    response = requests.get(url)
    if response.status_code == 200:
        result = response.json()
    else:
        raise Exception(f"Failed to fetch data from {url}: {response.status_code}: {response.text}")
    return result


@contextmanager
def smart_open(file, *args, **kwargs):
    """
    Open a file, or use stdin/stdout if file is '-'.
    Passes all additional args/kwargs to open().
    """
    if str(file) == '-':
        sys.stdout.reconfigure(encoding='utf-8')
        yield sys.stdout
    else:
        with open(file, *args, **kwargs) as f:
            yield f
