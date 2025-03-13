class TokenValidationError(Exception):
    """A failure to validate an access token."""


class AuthenticationError(Exception):
    """A failure to authenticate a user."""
