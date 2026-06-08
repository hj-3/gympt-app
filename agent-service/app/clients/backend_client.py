import httpx
import logging
from typing import Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.config import settings

logger = logging.getLogger(__name__)


class AsyncBackendClient:
    """Async HTTP client for Backend API integration."""

    def __init__(self):
        self.base_url = settings.backend_api_base_url
        self.timeout = settings.backend_api_timeout
        self.max_retries = 3
        self.backoff_factor = 2

    def _get_headers(self, internal_token: Optional[str] = None) -> Dict[str, str]:
        """
        Build request headers.

        Args:
            internal_token: JWT token from X-Internal-Token header

        Returns:
            Headers dict
        """
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "gympt-agent-service"
        }

        if internal_token:
            headers["Authorization"] = f"Bearer {internal_token}"

        return headers

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
        reraise=True
    )
    async def get_user_profile(
        self,
        user_id: str,
        internal_token: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch user profile from Backend API.

        Args:
            user_id: User identifier
            internal_token: JWT token for internal API authentication

        Returns:
            User profile data or None if failed
        """
        try:
            url = f"{self.base_url}/api/v1/users/{user_id}/profile"
            headers = self._get_headers(internal_token)

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()

                data = response.json()
                logger.info(f"Fetched user profile: user_id={user_id}")
                return data

        except httpx.HTTPStatusError as e:
            logger.error(
                f"Failed to fetch user profile: user_id={user_id}, "
                f"status={e.response.status_code}"
            )
            return None
        except httpx.TimeoutException:
            logger.error(f"Timeout fetching user profile: user_id={user_id}")
            raise
        except httpx.ConnectError:
            logger.error(f"Connection error fetching user profile: user_id={user_id}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching user profile: {e}")
            return None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
        reraise=True
    )
    async def get_body_profile(
        self,
        user_id: str,
        internal_token: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch user body profile from Backend API.

        Args:
            user_id: User identifier
            internal_token: JWT token for internal API authentication

        Returns:
            Body profile data or None if failed
        """
        try:
            url = f"{self.base_url}/api/v1/users/{user_id}/body-profile"
            headers = self._get_headers(internal_token)

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()

                data = response.json()
                logger.info(f"Fetched body profile: user_id={user_id}")
                return data

        except httpx.HTTPStatusError as e:
            logger.error(
                f"Failed to fetch body profile: user_id={user_id}, "
                f"status={e.response.status_code}"
            )
            return None
        except httpx.TimeoutException:
            logger.error(f"Timeout fetching body profile: user_id={user_id}")
            raise
        except httpx.ConnectError:
            logger.error(f"Connection error fetching body profile: user_id={user_id}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching body profile: {e}")
            return None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
        reraise=True
    )
    async def get_workout_goals(
        self,
        user_id: str,
        internal_token: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch user workout goals from Backend API.

        Args:
            user_id: User identifier
            internal_token: JWT token for internal API authentication

        Returns:
            Workout goals data or None if failed
        """
        try:
            url = f"{self.base_url}/api/v1/users/{user_id}/goals"
            headers = self._get_headers(internal_token)

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()

                data = response.json()
                logger.info(f"Fetched workout goals: user_id={user_id}")
                return data

        except httpx.HTTPStatusError as e:
            logger.error(
                f"Failed to fetch workout goals: user_id={user_id}, "
                f"status={e.response.status_code}"
            )
            return None
        except httpx.TimeoutException:
            logger.error(f"Timeout fetching workout goals: user_id={user_id}")
            raise
        except httpx.ConnectError:
            logger.error(f"Connection error fetching workout goals: user_id={user_id}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching workout goals: {e}")
            return None

    async def get_user_data(
        self,
        user_id: str,
        internal_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fetch all user data (profile, body profile, goals) in parallel.

        Args:
            user_id: User identifier
            internal_token: JWT token for internal API authentication

        Returns:
            Combined user data dict
        """
        import asyncio

        try:
            # Fetch all data in parallel
            profile, body_profile, goals = await asyncio.gather(
                self.get_user_profile(user_id, internal_token),
                self.get_body_profile(user_id, internal_token),
                self.get_workout_goals(user_id, internal_token),
                return_exceptions=True
            )

            return {
                "profile": profile if not isinstance(profile, Exception) else None,
                "body_profile": body_profile if not isinstance(body_profile, Exception) else None,
                "goals": goals if not isinstance(goals, Exception) else None
            }

        except Exception as e:
            logger.error(f"Failed to fetch user data: {e}")
            return {
                "profile": None,
                "body_profile": None,
                "goals": None
            }


# Singleton instance
backend_client = AsyncBackendClient()
