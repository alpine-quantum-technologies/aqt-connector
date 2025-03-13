from dataclasses import dataclass

from auth0.authentication import token_verifier  # type: ignore

from aqt_connector.exceptions import TokenValidationError


@dataclass
class AccessTokenVerifierConfig:
    """Configuration for an instance of AccessTokenVerifier."""

    jwks_url: str
    expected_issuer: str
    allowed_audiences: list[str]


class AccessTokenVerifier:
    """A verifier for OIDC access tokens.

    Attributes:
        jwks_url (str): the URL for the token issuer's JWKS.
        expected_issuer (str): the expected *iss* claim of the token.
        allowed_audiences (list[str]): a list of possible *aud* claims that would be valid for
            the application.
    """

    def __init__(self, config: AccessTokenVerifierConfig) -> None:
        """Initialises the instance based on the given config.

        Args:
            config (AccessTokenVerifierConfig): Defines the config for the instance.
        """
        self.jwks_url = config.jwks_url
        self.issuer = config.expected_issuer
        self.allowed_audiences = config.allowed_audiences

    def verify_access_token(self, access_token: str) -> str:
        """Verifies an access token and its precedence.

        Args:
            access_token (str): The access token to validate.

        Raises:
            TokenValidationError: when the access token cannot be verified, or is invalid.

        Returns:
            The verified access token.
        """
        sv = token_verifier.AsymmetricSignatureVerifier(self.jwks_url)

        for audience in self.allowed_audiences:
            tv = token_verifier.TokenVerifier(signature_verifier=sv, issuer=self.issuer, audience=audience)
            try:
                tv.verify(access_token)
            except (token_verifier.TokenValidationError, KeyError):
                continue
            return access_token

        raise TokenValidationError
