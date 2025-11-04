from aqt_connector._domain.auth_service import AuthService
from aqt_connector._domain.oidc_service import OIDCService
from aqt_connector._infrastructure.access_token_verifier import AccessTokenVerifier, AccessTokenVerifierConfig
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

        self.oidc_service = OIDCService(Auth0Adapter(config.oidc_config), token_verifier)
        self.auth_service = AuthService(token_verifier, TokenRepository(config._app_dir), self.oidc_service)
