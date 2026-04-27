"""
redshift_toolkit — personal offensive security Python toolkit.

Grows module by module through the Redshift ethical-hacking curriculum.
Sub-packages are imported lazily; nothing is loaded at package import time.

Example
-------
    >>> from redshift_toolkit.utils.encoder_decoder import b64
    >>> b64("admin:admin")
    'YWRtaW46YWRtaW4='
"""
__version__ = "0.1.0"

__all__ = [
    "recon", "scan", "web", "net", "payload", "creds", "ad", "postex",
    "cloud", "mobile", "ics", "c2", "evasion", "forensics", "automation",
    "utils",
]
