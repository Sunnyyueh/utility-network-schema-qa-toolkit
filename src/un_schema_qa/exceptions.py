"""Public exception hierarchy for the toolkit."""


class ToolkitError(Exception):
    """Base class for errors that can be presented directly to users."""


class ConfigurationError(ToolkitError):
    """Raised when a project manifest is invalid."""


class InputFormatError(ToolkitError):
    """Raised when a structured input cannot be interpreted."""


class WorkbookDetectionError(InputFormatError):
    """Raised when an Excel workbook cannot be identified unambiguously."""


class ValidationExecutionError(ToolkitError):
    """Raised when a validator cannot complete safely."""
