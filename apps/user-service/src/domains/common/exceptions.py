class DomainError(Exception):
    code = "domain_error"

class DuplicateEmail(DomainError):
    code = "duplicate_email"

class DuplicateUsername(DomainError):
    code = "duplicate_username"

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
