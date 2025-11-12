class TokenValidationError(ValueError):
    """A failure to validate an access token."""


class AuthenticationError(PermissionError):
    """A failure to authenticate a user."""


class NotAuthenticatedError(PermissionError):
    """A failure to complete operation that requires authentication, as no user is authenticated."""


class JobNotFoundError(ValueError):
    """A failure due to querying a job that doesn't exist."""


class JobExpiredError(ValueError):
    """A failure to query a job's state as it has expired."""


class InvalidJobIDError(ValueError):
    """A failure due to querying an invalid job ID."""


class UnknownServerError(RuntimeError):
    """A failure due to an unknown server error."""


class RequestError(ConnectionError):
    """A failure due to issues with a request."""
