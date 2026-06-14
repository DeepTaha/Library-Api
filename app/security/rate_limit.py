"""Shared rate-limiter instance and IP key function."""
from slowapi import Limiter
from slowapi.util import get_remote_address

# Key on the real client IP.  Behind a trusted reverse proxy, replace
# get_remote_address with a function that reads X-Forwarded-For.
limiter = Limiter(key_func=get_remote_address)
