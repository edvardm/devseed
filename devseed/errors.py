class Error(Exception):
    """Base class for all devseed errors"""

    def __init__(self, message, detail=None):
        self.message = message
        self.detail = detail

    def __str__(self):
        msgs = (msg for msg in [self.message, self.detail] if msg is not None)
        return " ".join(msgs)


class InvalidEntry(Error):
    pass


class DatabaseError(Error):
    pass
