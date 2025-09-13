# URL_PARSERS package
# This file makes the URL_PARSERS directory a Python package

from .http_headers import extract_url_and_headers, add_http_headers_to_ytdl_opts

__all__ = ['extract_url_and_headers', 'add_http_headers_to_ytdl_opts'] 