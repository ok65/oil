

class CommsTimeoutError(Exception):
    pass


class PyVisaConfigError(Exception):
    pass


class InstrumentIdentityError(Exception):
    """Raised when a connected instrument does not match its expected model."""
