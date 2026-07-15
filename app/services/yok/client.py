from __future__ import annotations

import time
from dataclasses import dataclass
from time import monotonic
from urllib.parse import urlencode, urlparse

import httpx


YOK_HOST = "akademik.yok.gov.tr"
YOK_BASE_URL = "https://akademik.yok.gov.tr/AkademikArama"
YOK_HOME_URL = f"{YOK_BASE_URL}/"
YOK_PROFILE_PATH = (
    f"{YOK_BASE_URL}/AkademisyenGorevOgrenimBilgileri"
)


class YokRequestError(RuntimeError):
    """YÖK Akademik sayfası alınamadığında oluşur."""


@dataclass(frozen=True)
class YokPage:
    url: str
    status_code: int
    html: str


class YokClient:
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
                "User-Agent": "DEU-Akademik-Rapor/0.2",
                "Accept": "text/html,application/xhtml+xml",
            },
        )

    def __enter__(self) -> YokClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    def open_academician_profile(
        self,
        *,
        author_id: str,
        profile_sira: str,
    ) -> YokPage:
        """
        Arama endpoint'ini kullanmadan, katalogdaki YÖK kimlikleriyle
        akademisyenin profil oturumunu başlatır.
        """
        clean_author_id = author_id.strip()
        clean_profile_sira = profile_sira.strip()

        if not clean_author_id:
            raise ValueError("YÖK authorId boş olamaz.")

        if not clean_profile_sira:
            raise ValueError("YÖK profil sira değeri boş olamaz.")

        self._client.cookies.clear()

        home_page = self.get_html(YOK_HOME_URL)

        profile_query = urlencode(
            {
                "islem": "direct",
                "sira": clean_profile_sira,
                "authorId": clean_author_id,
            }
        )
        profile_url = f"{YOK_PROFILE_PATH}?{profile_query}"

        return self.get_html(
            profile_url,
            referer_url=home_page.url,
        )

    def get_html(
        self,
        url: str,
        *,
        referer_url: str | None = None,
    ) -> YokPage:
        self._validate_yok_url(url)

        if referer_url is not None:
            self._validate_yok_url(referer_url)

        self._wait_before_next_request()

        request_headers: dict[str, str] = {}

        if referer_url is not None:
            request_headers["Referer"] = referer_url

        try:
            response = self._client.get(
                url,
                headers=request_headers,
            )
            response.raise_for_status()
        except httpx.HTTPError as error:
            raise YokRequestError(
                f"YÖK Akademik sayfası alınamadı: {url}"
            ) from error

        return self._build_page(response)

    def _build_page(self, response: httpx.Response) -> YokPage:
        content_type = response.headers.get("content-type", "")

        if "html" not in content_type.casefold():
            raise YokRequestError(
                "YÖK Akademik HTML yerine farklı içerik döndü."
            )

        self._last_request_at = monotonic()

        return YokPage(
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
    def _validate_yok_url(url: str) -> None:
        parsed_url = urlparse(url)

        if parsed_url.scheme != "https" or parsed_url.netloc != YOK_HOST:
            raise ValueError(
                "Yalnızca https://akademik.yok.gov.tr adresleri "
                "tarama için kullanılabilir."
            )