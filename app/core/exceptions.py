class ApplicationException(Exception):
    """Base exception for all application-level errors."""

    def __init__(self, message: str = "An application error occurred", status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class BusinessRuleException(ApplicationException):
    """Raised when a business rule is violated."""

    def __init__(self, message: str = "A business rule was violated"):
        super().__init__(message=message, status_code=422)


class NotFoundException(ApplicationException):
    """Raised when a requested resource is not found."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message=message, status_code=404)


class InfrastructureError(ApplicationException):
    """Raised when an infrastructure-level error occurs (DB, external service, etc.)."""

    def __init__(self, message: str = "An infrastructure error occurred"):
        super().__init__(message=message, status_code=500)


class AuthenticationError(ApplicationException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message=message, status_code=401)
