import time
from enum import Enum
from typing import Optional
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class CircuitBreakerState(Enum):

    """
    State Transitions:
    1. CLOSED → OPEN: When failure count reaches threshold
    2. OPEN → HALF_OPEN: After reset timeout period
    3. HALF_OPEN → CLOSED: On successful request
    4. HALF_OPEN → OPEN: On failed request
    """
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"



class CircuitBreaker:
    """
    Circuit Breaker Implementation
    """

    def __init__(self,failure_threshold:int = 5,reset_timeout:int = 30):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time:Optional[float] = None

        self.logger = setup_logger(__name__)
        self.logger.info(f"Circuit breaker initialized with threshold={failure_threshold}, timeout={reset_timeout}")

    def can_execute(self) -> bool:
        """
        Check if the circuit breaker allows execution.
        """
        if self.state == CircuitBreakerState.CLOSED:
            return True
        elif self.state == CircuitBreakerState.OPEN:
            if self.last_failure_time is None:
                self.logger.warning("Circuit breaker in OPEN state but no failure time recorded")
                return False
            time_since_failure = time.time() - self.last_failure_time
            if time_since_failure >= self.reset_timeout:
                self._transition_to_half_open()
                self.logger.info("Circuit breaker transitioning to HALF_OPEN state")
                return True
            else:
                remaining_time = self.reset_timeout - time_since_failure
                self.logger.debug(f"Circuit breaker still OPEN, {remaining_time:.1f}s remaining")
                return False
        elif self.state == CircuitBreakerState.HALF_OPEN:
            return True
        else:
            self.logger.error(f"Invalid circuit breaker state: {self.state}")
            return False
            
    def record_success(self):
        """
        Record a successful operation.
        """
        if self.state == CircuitBreakerState.CLOSED:
            if self.failure_count > 0:
                self.failure_count = 0
                self.logger.debug("Success in CLOSED state, reset failure count")
            self.success_count += 1
            self.logger.debug(f"Success in CLOSED state, success count: {self.success_count}")
        elif self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            self._transition_to_closed()
            self.logger.info("Success in HALF_OPEN state, transitioning to CLOSED")
        elif self.state == CircuitBreakerState.OPEN:
            self.logger.warning("Success recorded while circuit breaker is OPEN")
            
    def record_failure(self):
        """
        Record a failed operation.
        """
        if self.state == CircuitBreakerState.CLOSED:
            self.failure_count += 1
            self.logger.debug(f"Failure in CLOSED state, failure count: {self.failure_count}")
            if self.failure_count >= self.failure_threshold:
                self._transition_to_open()
                self.logger.warning(f"Failure threshold reached ({self.failure_threshold}), transitioning to OPEN")
        elif self.state == CircuitBreakerState.HALF_OPEN:
            self._transition_to_open()
            self.logger.warning("Failure in HALF_OPEN state, transitioning back to OPEN")
        elif self.state == CircuitBreakerState.OPEN:
            self.logger.warning("Failure recorded while circuit breaker is OPEN")
            
    def _transition_to_open(self):
        """
        Transition circuit breaker to OPEN state.
        """
        self.state = CircuitBreakerState.OPEN
        self.last_failure_time = time.time()
        self.success_count = 0
        self.logger.warning("Circuit breaker transitioning to OPEN state")

    def _transition_to_half_open(self):
        """
        Transition circuit breaker to HALF_OPEN state.
        """
        self.state = CircuitBreakerState.HALF_OPEN
        self.success_count = 0
        self.logger.info("Circuit breaker transitioning to HALF_OPEN state")

    def _transition_to_closed(self):
        """
        Transition circuit breaker to CLOSED state.
        """
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.logger.info("Circuit breaker transitioned to CLOSED state")


    def reset(self):
        """
        Manually reset the circuit breaker to CLOSED state.        
        """
        self._transition_to_closed()
        self.logger.info("Circuit breaker manually reset to CLOSED state")

    
    def get_status(self) -> dict:
        """
        Get detailed status information about the circuit breaker.
        
        """
        status = {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "can_execute": self.can_execute(),
        }
        
        if self.last_failure_time is not None:
            status["time_since_last_failure"] = time.time() - self.last_failure_time
            status["remaining_timeout"] = max(0, self.reset_timeout - status["time_since_last_failure"])
        else:
            status["time_since_last_failure"] = None
            status["remaining_timeout"] = None
        
        return status
