"""
Shared token-bucket rate limiter.

Piece 6 — written by hand:
  - token_bucket.lua : read -> lazy refill -> check -> decrement, atomically
  - check(redis, key, capacity, refill_rate) -> (allowed, remaining, retry_after)

Used by:
  - limiter service  (HTTP wrapper, for POST /shorten)
  - shortener        (direct call, for GET /{code})
"""
