"""Authentication type enumeration."""

from enum import Enum


class AuthType(str, Enum):
    """Authentication type enumeration."""

    BASIC = "BASIC"
    BEARER = "BEARER"
