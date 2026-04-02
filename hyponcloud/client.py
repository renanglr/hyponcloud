"""Hypontech Cloud API client."""

import asyncio
import json
import logging
from time import time
from typing import Any, cast

import aiohttp

from .exceptions import AuthenticationError, RateLimitError, RequestError
from .models import AdminInfo, InverterData, OverviewData, PlantData, PlantMonitorData

_LOGGER = logging.getLogger(__name__)


class HyponCloud:
    """HyponCloud API client."""

    def __init__(
        self,
        username: str,
        password: str,
        session: aiohttp.ClientSession | None = None,
        timeout: int = 10,
        retries: int = 3,
        debug: bool = False,
    ) -> None:
        """Initialize the HyponCloud class.

        Args:
            username: The username for Hypon Cloud.
            password: The password for Hypon Cloud.
            session: Optional aiohttp client session. If not provided, a new
                one will be created.
            timeout: Request timeout in seconds. Defaults to 10.
            retries: Number of retry attempts for API requests. Defaults to 3.
            debug: Enable debug mode to print raw HTTP responses. Defaults to False.
        """
        self.base_url = "https://api.hypon.cloud/v2"
        self.token_validity = 3600
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.retries = retries
        self.debug = debug

        self._session = session
        self._own_session = session is None
        self.__username = username
        self.__password = password
        self.__token = ""
        self.__token_expires_at = 0

    async def __aenter__(self) -> "HyponCloud":
        """Async context manager entry."""
        if self._own_session:
            self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        if self._own_session and self._session:
            await self._session.close()

    async def close(self) -> None:
        """Close the session if we own it."""
        if self._own_session and self._session:
            await self._session.close()

    async def connect(self) -> None:
        """Connect to Hypon Cloud and retrieve token.

        Raises:
            AuthenticationError: If authentication fails.
            ConnectionError: If connection to API fails.
        """
        if self.__token and self.__token_expires_at > time():
            return

        if not self._session:
            self._session = aiohttp.ClientSession()
            self._own_session = True

        url = f"{self.base_url}/login"
        data = {"username": self.__username, "password": self.__password}

        try:
            async with self._session.post(
                url, json=data, timeout=self.timeout
            ) as response:
                result = await self._parse_response(response, "POST", url)

                if response.status == 401:
                    raise AuthenticationError("Invalid credentials")
                if response.status == 429:
                    raise RateLimitError(
                        "Rate limit exceeded. Requests are being sent too fast."
                    )
                if response.status != 200:
                    raise RequestError(
                        f"Connection failed with status {response.status}"
                    )

                self.__token = result["data"]["token"]
                self.__token_expires_at = int(time()) + self.token_validity
        except aiohttp.ClientError as e:
            raise RequestError(f"Failed to connect to Hypon Cloud: {e}") from e
        except KeyError as e:
            raise AuthenticationError(
                f"Invalid response from API, missing token: {e}"
            ) from e

    async def _parse_response(
        self, response: aiohttp.ClientResponse, method: str, url: str
    ) -> dict:
        """Parse response, optionally printing debug info."""
        if self.debug:
            print(f"\n=== {method} {url} ===")
            print(f"Status: {response.status}")
            print(f"Headers: {dict(response.headers)}")
            raw_text = await response.text()
            print(f"Response: {raw_text}")
            return cast(dict, json.loads(raw_text))
        return cast(dict, await response.json())

    async def _request(
        self, url: str, endpoint_name: str, retries: int | None = None
    ) -> dict:
        """Make an authenticated GET request with retry logic.

        Args:
            url: The URL to request.
            endpoint_name: Human-readable name for error messages.
            retries: Number of retry attempts. Defaults to client's setting.

        Returns:
            Parsed JSON response dict.

        Raises:
            RateLimitError: If rate limit is exceeded and retries are exhausted.
            RequestError: If request fails and retries are exhausted.
        """
        retries = retries if retries is not None else self.retries
        await self.connect()
        assert self._session is not None  # connect() ensures session exists

        headers = {"authorization": f"Bearer {self.__token}"}
        try:
            async with self._session.get(
                url, headers=headers, timeout=self.timeout
            ) as response:
                result = await self._parse_response(response, "GET", url)

                if response.status == 429:
                    if retries > 0:
                        await asyncio.sleep(10)
                        return await self._request(url, endpoint_name, retries - 1)
                    raise RateLimitError(f"Rate limit exceeded for {endpoint_name}")

                if response.status != 200:
                    if retries > 0:
                        await asyncio.sleep(10)
                        return await self._request(url, endpoint_name, retries - 1)
                    raise RequestError(
                        f"Failed to get {endpoint_name}: HTTP {response.status}"
                    )

                return result
        except aiohttp.ClientError as e:
            raise RequestError(f"Failed to get {endpoint_name}: {e}") from e

    async def get_overview(self, retries: int | None = None) -> OverviewData:
        """Get plant overview.

        Args:
            retries: Number of retry attempts if request fails. If None,
                uses the client's default retry setting.

        Returns:
            OverviewData object containing plant overview information.

        Raises:
            AuthenticationError: If authentication fails.
            ConnectionError: If connection to API fails.
        """
        retries = retries if retries is not None else self.retries
        url = f"{self.base_url}/plant/overview"
        try:
            result = await self._request(url, "plant overview", retries)
            return OverviewData.from_dict(result["data"])
        except KeyError as e:
            _LOGGER.error("Error parsing plant overview data: %s", e)
            if retries > 0:
                return await self.get_overview(retries - 1)
            return OverviewData()

    async def get_list(self, retries: int | None = None) -> list[PlantData]:
        """Get plant list.

        Args:
            retries: Number of retry attempts if request fails. If None,
                uses the client's default retry setting.

        Returns:
            List of PlantData objects.

        Raises:
            AuthenticationError: If authentication fails.
            ConnectionError: If connection to API fails.
        """
        url = f"{self.base_url}/plant/list2?page=1&page_size=10&refresh=true"
        try:
            result = await self._request(url, "plant list", retries)
            return [PlantData.from_dict(item) for item in result["data"]]
        except Exception as e:
            _LOGGER.error("Error getting plant list: %s", e)
            raise RequestError(f"Failed to get plant list: {e}") from e

    async def get_inverters(
        self, plant_id: str, retries: int | None = None
    ) -> list[InverterData]:
        """Get all inverters for a specific plant.

        This method automatically fetches all pages of inverters.

        Args:
            plant_id: The plant ID to get inverters for.
            retries: Number of retry attempts if request fails. If None,
                uses the client's default retry setting.

        Returns:
            List of all InverterData objects across all pages.

        Raises:
            AuthenticationError: If authentication fails.
            ConnectionError: If connection to API fails.
        """
        retries = retries if retries is not None else self.retries
        all_inverters: list[InverterData] = []
        page = 1
        total_pages = 1

        while page <= total_pages:
            url = f"{self.base_url}/plant/{plant_id}/inverter?page={page}"
            try:
                result = await self._request(url, "inverter list", retries)
                if "totalPage" in result:
                    total_pages = result["totalPage"]
                all_inverters.extend(
                    InverterData.from_dict(item) for item in result["data"]
                )
                page += 1
            except KeyError as e:
                _LOGGER.error("Error parsing inverter list data: %s", e)
                if retries > 0:
                    return await self.get_inverters(plant_id, retries - 1)
                return []

        return all_inverters

    async def get_monitor(
        self, plant_id: str, retries: int | None = None
    ) -> PlantMonitorData:
        """Get real-time monitoring data for a specific plant.

        Args:
            plant_id: The plant ID to get monitoring data for.
            retries: Number of retry attempts if request fails. If None,
                uses the client's default retry setting.

        Returns:
            PlantMonitorData object containing plant monitoring information.

        Raises:
            AuthenticationError: If authentication fails.
            ConnectionError: If connection to API fails.
        """
        url = f"{self.base_url}/plant/{plant_id}/monitor?refresh=true"
        try:
            result = await self._request(url, "plant monitor", retries)
            return PlantMonitorData.from_dict(result["data"])
        except KeyError as e:
            _LOGGER.error("Error parsing plant monitor data: %s", e)
            return PlantMonitorData()

    async def get_admin_info(self, retries: int | None = None) -> AdminInfo:
        """Get administrator information.

        Args:
            retries: Number of retry attempts if request fails. If None,
                uses the client's default retry setting.

        Returns:
            AdminInfo object containing administrator information.

        Raises:
            AuthenticationError: If authentication fails.
            ConnectionError: If connection to API fails.
        """
        retries = retries if retries is not None else self.retries
        url = f"{self.base_url}/administrator/admininfo"
        try:
            result = await self._request(url, "admin info", retries)
            data = result["data"]
            # Flatten nested "info" object into the main data dict
            if "info" in data and isinstance(data["info"], dict):
                info_data = data.pop("info")
                data.update(info_data)
            return AdminInfo.from_dict(data)
        except KeyError as e:
            _LOGGER.error("Error parsing admin info data: %s", e)
            if retries > 0:
                return await self.get_admin_info(retries - 1)
            return AdminInfo()
