from __future__ import annotations

import time
from dataclasses import dataclass
from time import monotonic
from urllib.parse import urlparse

import httpx


AVESIS_HOST = "avesis.deu.edu.tr"


class AvesisRequestError(RuntimeError):
    """AVESİS'ten sayfa alınamadığında oluşur."""


@dataclass(frozen=True)
class AvesisPage:
    url: str
    status_code: int
    html: str


class AvesisClient:
    def __init__(
        self,
        timeout_seconds: float = 30.0,
        request_delay_seconds: float = 0.75,
    ) -> None:
        self._request_delay_seconds = request_delay_seconds
        self._last_request_at: float | None = None
        self._client = httpx.Client(
            timeout=httpx.Timeout(timeout_seconds),
            follow_redirects=True,
            headers={
                "User-Agent": "DEU-Avesis-Academic-Report/0.1",
                "Accept": "text/html,application/xhtml+xml",
            },
        )

    def __enter__(self) -> AvesisClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    def get_publications(self, profile_url: str) -> AvesisPage:
        return self.get_html(f"{profile_url.rstrip('/')}/yayinlar")

    def get_projects(self, profile_url: str) -> AvesisPage:
        return self.get_html(f"{profile_url.rstrip('/')}/projeler")

    def get_html(self, url: str) -> AvesisPage:
        self._validate_avesis_url(url)
        self._wait_before_next_request()

        try:
            response = self._client.get(url)
            response.raise_for_status()
        except httpx.HTTPError as error:
            raise AvesisRequestError(
                f"AVESİS sayfası alınamadı: {url}"
            ) from error

        content_type = response.headers.get("content-type", "")

        if "html" not in content_type.casefold():
            raise AvesisRequestError(
                f"AVESİS HTML yerine farklı içerik döndü: {url}"
            )

        self._last_request_at = monotonic()

        return AvesisPage(
            url=str(response.url),
            status_code=response.status_code,
            html=response.text,
        )

    def _wait_before_next_request(self) -> None:
        if self._last_request_at is None:
            return

        elapsed = monotonic() - self._last_request_at
        remaining = self._request_delay_seconds - elapsed

        if remaining > 0:
            time.sleep(remaining)

    @staticmethod
    def _validate_avesis_url(url: str) -> None:
        parsed_url = urlparse(url)

        if parsed_url.scheme != "https" or parsed_url.netloc != AVESIS_HOST:
            raise ValueError(
                "Yalnızca https://avesis.deu.edu.tr adresleri taranabilir."
            )