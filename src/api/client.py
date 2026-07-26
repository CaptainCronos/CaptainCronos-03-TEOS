"""Convenience client retaining the facade's stable synchronous semantics."""

from .facade import TEOSApplication


class TEOSClient(TEOSApplication):
    """Compatibility name for applications that prefer a client vocabulary."""

