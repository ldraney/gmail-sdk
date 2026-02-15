from importlib.metadata import version

from .client import GmailClient, GmailAPIError

__version__ = version("gmail-sdk-ldraney")
__all__ = ["GmailClient", "GmailAPIError", "__version__"]
