"""
Custom exceptions for the DAO GolemDB system.
"""


class GolemDBError(Exception):
    """Base exception for GolemDB operations."""
    pass


class ConnectionError(GolemDBError):
    """Raised when connection to GolemDB fails."""
    pass


class InsufficientBalanceError(GolemDBError):
    """Raised when account has insufficient balance."""
    pass


class EntityNotFoundError(GolemDBError):
    """Raised when entity is not found in GolemDB."""
    pass


class UploadError(GolemDBError):
    """Raised when file upload fails."""
    pass


class DownloadError(GolemDBError):
    """Raised when file download fails."""
    pass


class SearchError(GolemDBError):
    """Raised when search operation fails."""
    pass


class ConfigurationError(Exception):
    """Raised when configuration is invalid."""
    pass