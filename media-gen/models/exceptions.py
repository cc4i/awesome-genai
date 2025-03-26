"""
Custom exceptions for the media generation application.
"""

class MediaGenerationError(Exception):
    """Base exception for media generation errors."""
    pass

class FileUploadError(MediaGenerationError):
    """Exception raised for file upload errors."""
    pass

class GenerationError(MediaGenerationError):
    """Exception raised for media generation errors."""
    pass

class ValidationError(MediaGenerationError):
    """Exception raised for input validation errors."""
    pass

class ConfigurationError(MediaGenerationError):
    """Exception raised for configuration errors."""
    pass 