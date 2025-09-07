class DomainError(Exception):
    code = "domain_error"

class NotFound(DomainError):
    code = "not_found"

class ValidationFailed(DomainError):
    code = "validation_failed"

class Unauthorized(DomainError):
    code = "unauthorized"

class Forbidden(DomainError):
    code = "forbidden"

class Conflict(DomainError):
    code = "conflict"

class DatabaseConflict(Exception):
    code = "db_conflict"
