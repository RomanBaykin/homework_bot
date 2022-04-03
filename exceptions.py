class MessageSendError(Exception):
    """raises when message can't be send."""

    pass


class EndpointNotFound(Exception):
    """Endpoint can't be found."""

    pass


class UnknownError(Exception):
    """Some unknown error."""

    pass
