import wsgiref.simple_server
from typing import Any, Callable, Literal, Mapping, Self, Sequence, Tuple

from _typeshed import Incomplete
from google.auth.transport.requests import AuthorizedSession
from google.oauth2.credentials import Credentials
from requests_oauthlib import OAuth2Session

class Flow:
    client_type: Literal["web", "installed"]
    client_config: Mapping[str, Any]
    oauth2session: OAuth2Session
    code_verifier: str
    autogenerate_code_verifier: bool

    def __init__(
        self,
        oauth2session: OAuth2Session,
        client_type: Literal["web", "installed"],
        client_config: Mapping[str, Any],
        redirect_uri: str | None = ...,
        code_verifier: str | None = ...,
        autogenerate_code_verifier: bool = ...,
    ) -> None: ...
    @classmethod
    def from_client_config(cls, client_config: Mapping[str, Any], scopes: Sequence[str], **kwargs: Any) -> Self: ...
    @classmethod
    def from_client_secrets_file(cls, client_secrets_file: str, scopes: Sequence[str], **kwargs: Any) -> Self: ...
    @property
    def redirect_uri(self) -> str: ...
    @redirect_uri.setter
    def redirect_uri(self, value: str) -> None: ...
    def authorization_url(self, **kwargs: Any) -> Tuple[str, str]: ...
    def fetch_token(self, **kwargs: Any) -> Mapping[str, str]: ...
    @property
    def credentials(self) -> Credentials: ...
    def authorized_session(self) -> AuthorizedSession: ...

class InstalledAppFlow(Flow):
    redirect_uri: str

    def run_local_server(
        self,
        host: str = ...,
        bind_addr: str | None = ...,
        port: int = ...,
        authorization_prompt_message: str | None = ...,
        success_message: str = ...,
        open_browser: bool = ...,
        redirect_uri_trailing_slash: bool = ...,
        timeout_seconds: int | None = ...,
        token_audience: str | None = ...,
        browser: str | None = ...,
        **kwargs: Any,
    ) -> Credentials: ...

class _WSGIRequestHandler(wsgiref.simple_server.WSGIRequestHandler):
    def log_message(self, format: str, *args: Any) -> None: ...

class _RedirectWSGIApp:
    last_request_uri: Incomplete

    def __init__(self, success_message: str) -> None: ...
    def __call__(self, environ: Mapping[str, Any], start_response: Callable[[str], list[Any]]) -> list[str]: ...
