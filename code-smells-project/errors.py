"""Expected API errors, mapped to HTTP in the view layer."""


class APIError(Exception):
    def __init__(self, message, status=400, success_field=False):
        super().__init__(message)
        self.message = message
        self.status = status
        self.success_field = success_field
