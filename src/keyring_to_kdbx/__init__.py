"""keyring-to-kdbx: Export system keyring secrets to KeePass database format."""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from keyring_to_kdbx.exporter import KeyringExporter

__all__ = ["KeyringExporter", "__version__"]
