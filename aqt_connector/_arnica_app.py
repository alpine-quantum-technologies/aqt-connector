from contextlib import ExitStack
from typing import Optional

from typing_extensions import Self

from aqt_connector._domain.auth_service import AuthService
from aqt_connector._domain.job_service import JobService
from aqt_connector._domain.oidc_service import OIDCService
from aqt_connector._infrastructure.access_token_verifier import AccessTokenVerifier, AccessTokenVerifierConfig
from aqt_connector._infrastructure.arnica_adapter import ArnicaAdapter
from aqt_connector._infrastructure.auth0_adapter import Auth0Adapter
from aqt_connector._infrastructure.token_repository import TokenRepository
from aqt_connector._sdk_config import ArnicaConfig

DEFAULT_CONFIG = ArnicaConfig()


class ArnicaApp:
    """Holds the initialization information for the application."""

    def __init__(self, config: ArnicaConfig = DEFAULT_CONFIG) -> None:
        """
        Args:
            config (ArnicaConfig, optional): the configuration for the instance. Defaults to
                an unmodified instance of `ArnicaConfig`.
        """
        self.config = config

        token_verifier = AccessTokenVerifier(
            AccessTokenVerifierConfig(
                jwks_url=config.oidc_config.jwks_url,
                expected_issuer=config.oidc_config.issuer,
                allowed_audiences=[config.arnica_url, config.oidc_config.device_client_id],
            )
        )

        with ExitStack() as stack:
            self._auth0_adapter = Auth0Adapter(config.oidc_config)
            stack.callback(self._auth0_adapter.close)
            self._arnica_adapter = ArnicaAdapter(self.config.arnica_url)
            stack.callback(self._arnica_adapter.close)

            self.oidc_service = OIDCService(self._auth0_adapter, token_verifier)
            self.auth_service = AuthService(token_verifier, TokenRepository(config._app_dir), self.oidc_service)
            self.job_service = JobService(self._arnica_adapter)

            stack.pop_all()

    def close(self) -> None:
        """Closes all underlying HTTP clients and releases their connection pools."""
        try:
            self._auth0_adapter.close()
        finally:
            self._arnica_adapter.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self, exc_type: Optional[type], exc_value: Optional[BaseException], traceback: Optional[object]
    ) -> Optional[bool]:
        self.close()
        return None
