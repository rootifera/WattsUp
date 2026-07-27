class NutError(Exception):
    """Base error raised by the NUT integration."""


class NutConnectionError(NutError):
    """The NUT server could not be reached."""


class NutProtocolError(NutError):
    """The NUT server returned an invalid or error response."""
