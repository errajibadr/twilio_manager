import logging
from typing import Dict, Optional, Tuple

import aiohttp
from twilio.http import HttpClient
from twilio.http.response import Response

_logger = logging.getLogger("twilio.async_http_client")

class AsyncTwilioHttpClient(HttpClient):
    """
    Async HTTP Client for interacting with the Twilio API
    """

    def __init__(
        self,
        timeout: Optional[float] = None,
        logger: logging.Logger = _logger,
        proxy: Optional[Dict[str, str]] = None,
    ):
        super().__init__(logger, True, timeout)  # Set is_async=True
        self.proxy = proxy if proxy else None
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, object]] = None,
        data: Optional[Dict[str, object]] = None,
        headers: Optional[Dict[str, str]] = None,
        auth: Optional[Tuple[str, str]] = None,
        timeout: Optional[float] = None,
        allow_redirects: bool = False,
    ) -> Response:
        """
        Make an async HTTP Request with parameters provided.
        """
        if timeout is None:
            timeout = self.timeout
        elif timeout <= 0:
            raise ValueError(timeout)

        if self.session is None:
            self.session = aiohttp.ClientSession()

        kwargs = {
            "url": url,
            "params": params,
            "headers": headers,
            "allow_redirects": allow_redirects,
            "timeout": aiohttp.ClientTimeout(total=timeout) if timeout else None,
        }

        if auth:
            kwargs["auth"] = aiohttp.BasicAuth(auth[0], auth[1])

        if headers and (
            headers.get("Content-Type") == "application/json"
            or headers.get("Content-Type") == "application/scim+json"
        ):
            kwargs["json"] = data
        else:
            kwargs["data"] = data

        if self.proxy:
            kwargs["proxy"] = self.proxy

        self.log_request({**kwargs, "method": method})

        async with self.session.request(method.upper(), **kwargs) as response:
            content = await response.text()
            self.log_response(response.status, response=response) # type: ignore

            twilioResponse = Response(
                int(response.status),
                content,
                dict(response.headers)
            )
            
            return twilioResponse 