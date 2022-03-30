class MessageSendError(Exception):
    """raises when message can't be send."""

    pass


class EndpointNotFound(Exception):
    """Endpoint can't be found."""

    pass
