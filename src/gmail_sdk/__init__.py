from importlib.metadata import version

from .client import GmailClient, GmailAPIError

__version__ = version("ldraney-gmail-sdk")
__all__ = ["GmailClient", "GmailAPIError", "__version__"]
