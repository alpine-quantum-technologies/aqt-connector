class TokenValidationError(Exception):
    """A failure to validate an access token."""


class AuthenticationError(Exception):
    """A failure to authenticate a user."""


class PermissionError(Exception):
    """A failure to authorize a user."""
