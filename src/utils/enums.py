from enum import Enum


class CircuitBreakerState(Enum):
    CLOSED = "CLOSED"  # Circuit is closed, requests are allowed
    OPEN = "OPEN"  # Circuit is open, requests are blocked
    HALF_OPEN = "HALF_OPEN"  # Circuit is half-open, requests are allowed after a delay


class SMSProvider(Enum):
    ARKESEL = "ARKESEL"
    MNOTIFY = "MNOTIFY"
