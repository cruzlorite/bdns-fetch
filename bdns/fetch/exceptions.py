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
Exception handling utilities for BDNS API
"""

import sys
import traceback
from typing import Optional

import typer


class BDNSError(Exception):
    """Base exception for BDNS operations"""

    def __init__(
        self,
        message: str,
        suggestion: Optional[str] = None,
        technical_details: Optional[str] = None,
    ):
        self.message = message
        self.suggestion = suggestion
        self.technical_details = technical_details
        super().__init__(self.message)


class BDNSWarning(BDNSError):
    """Warning for 200 OK but empty results"""

    pass


def parse_bdns_error_response(response_text: str) -> tuple[str, list[str]]:
    """
    Parse BDNS API error responses to extract structured error information
    Returns (error_code, error_messages)
    """
    try:
        import json

        error_data = json.loads(response_text)

        if isinstance(error_data, dict):
            # Extract error code
            error_code = error_data.get("codigo", "UNKNOWN_ERROR")

            # Extract error messages
            error_messages = []
            if "errores" in error_data and isinstance(error_data["errores"], list):
                error_messages = error_data["errores"]
            elif "error" in error_data:
                error_messages = [str(error_data["error"])]
            elif "message" in error_data:
                error_messages = [str(error_data["message"])]
            elif "detail" in error_data:
                error_messages = [str(error_data["detail"])]

            return error_code, error_messages

    except (json.JSONDecodeError, Exception):
        pass

    # Fallback: return raw response
    return "PARSE_ERROR", [
        response_text[:200] if response_text else "No error details available"
    ]


def format_bdns_error_message(error_code: str, error_messages: list[str]) -> str:
    """Format BDNS error messages in a beautiful way"""
    if not error_messages:
        return "Server returned an error (no details provided)"

    # Use the original error code as the error type
    error_type = (
        f"Error ({error_code})" if error_code != "PARSE_ERROR" else "Server Error"
    )

    # Keep all messages in their original language (Spanish)
    if len(error_messages) == 1:
        return f"{error_type}: {error_messages[0]}"
    else:
        # Multiple errors - format as numbered list
        formatted_errors = []
        for i, msg in enumerate(error_messages, 1):
            formatted_errors.append(f"  {i}. {msg}")

        return f"{error_type}:\n" + "\n".join(formatted_errors)


def handle_api_response(
    status_code: int, url: str, response_text: str = "", response_headers: dict = None
):
    """Handle API responses and decide what to do"""

    # Build technical details for debug mode
    tech_details = f"HTTP {status_code} from {url}"

    # Show first 100 chars of response content if present
    if response_text:
        content_preview = response_text[:100]
        if len(response_text) > 100:
            content_preview += "..."
        tech_details += f"\nResponse content (first 100 chars): {content_preview}"

    # Show headers in debug mode
    if response_headers:
        tech_details += "\nResponse headers:"
        for key, value in response_headers.items():
            tech_details += f"\n  {key}: {value}"

    if status_code == 200:
        # 200 OK but empty result - show warning
        return BDNSWarning(
            message="No data available for the specified parameters.",
            suggestion="This might be expected if no records match your criteria. Try different parameters.",
            technical_details=tech_details,
        )

    elif status_code == 204:
        # 204 No Content - also a warning (expected)
        return BDNSWarning(
            message="No data available for the specified parameters.",
            suggestion="This might be expected if no records match your criteria. Try different parameters.",
            technical_details=tech_details,
        )

    else:
        # Not 200/204 - something went wrong
        # Parse BDNS-specific error format for better user experience
        error_code, error_messages = parse_bdns_error_response(response_text)

        # Use HTTP status code names for error types
        if status_code == 400:
            message = (
                format_bdns_error_message(error_code, error_messages)
                if error_messages
                else "Bad Request"
            )
            suggestion = "Check your parameter values and formats. Use --help to see valid parameter examples."
        elif status_code == 401:
            message = (
                format_bdns_error_message(error_code, error_messages)
                if error_messages
                else "Unauthorized"
            )
            suggestion = "This endpoint may require authentication."
        elif status_code == 403:
            message = (
                format_bdns_error_message(error_code, error_messages)
                if error_messages
                else "Forbidden"
            )
            suggestion = "You don't have permission to access this resource."
        elif status_code == 404:
            message = (
                format_bdns_error_message(error_code, error_messages)
                if error_messages
                else "Not Found"
            )
            suggestion = "Check if the endpoint URL is correct or if the requested resource exists."
        elif status_code == 429:
            message = (
                format_bdns_error_message(error_code, error_messages)
                if error_messages
                else "Too Many Requests"
            )
            suggestion = (
                "Wait a moment and try again, or reduce --max-concurrent-requests."
            )
        elif status_code >= 500:
            message = (
                format_bdns_error_message(error_code, error_messages)
                if error_messages
                else "Internal Server Error"
            )
            suggestion = "The API server is experiencing issues. Try again later."
        else:
            message = format_bdns_error_message(error_code, error_messages)
            suggestion = "Check your internet connection and try again."

        return BDNSError(
            message=message, suggestion=suggestion, technical_details=tech_details
        )


def show_error(error: Exception, debug: bool = False) -> None:
    """Display error message to user, with optional technical details"""

    if isinstance(error, BDNSWarning):
        # Warning message (not an error)
        typer.secho(f"ℹ️  {error.message}", fg=typer.colors.YELLOW, err=True)

        if error.suggestion:
            typer.secho(f"💡 {error.suggestion}", fg=typer.colors.CYAN, err=True)

        if debug and error.technical_details:
            typer.secho("\nResponse Details:", fg=typer.colors.BLUE, err=True)
            typer.secho(error.technical_details, fg=typer.colors.BRIGHT_BLACK, err=True)

    elif isinstance(error, BDNSError):
        # Actual error message
        typer.secho(f"❌ {error.message}", fg=typer.colors.RED, err=True)

        if error.suggestion:
            typer.secho(f"💡 {error.suggestion}", fg=typer.colors.YELLOW, err=True)

        if debug and error.technical_details:
            typer.secho("\nResponse Output:", fg=typer.colors.BLUE, err=True)
            typer.secho(error.technical_details, fg=typer.colors.BRIGHT_BLACK, err=True)

    else:
        # For unexpected errors, show generic message unless debug mode
        if debug:
            typer.secho(
                f"❌ Unexpected error: {str(error)}", fg=typer.colors.RED, err=True
            )
            typer.secho("\nFull traceback:", fg=typer.colors.BLUE, err=True)
            traceback.print_exc(file=sys.stderr)
        else:
            typer.secho(
                "❌ An unexpected error occurred. Use --debug for technical details.",
                fg=typer.colors.RED,
                err=True,
            )


# For backward compatibility - keep the old function name but redirect to new one
def handle_api_error(
    status_code: int, url: str, response_text: str = "", response_headers: dict = None
):
    """Legacy function name - redirects to handle_api_response"""
    return handle_api_response(status_code, url, response_text, response_headers)
