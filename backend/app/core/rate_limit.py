"""
Shared rate limiter (slowapi, backed by the `limits` library). Keyed by
client IP by default. Applied per-endpoint - see main.py for the global
default and individual endpoint files for AI-calling routes that get a
stricter limit (those are the expensive ones - each call burns Gemini/Groq
quota or credits).
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])
