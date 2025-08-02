from abc import ABC, abstractmethod
from src.schema import SMSRequest, SMSResponse
from src.utils.circuit_breaker import CircuitBreaker
from typing import Dict, Any
from src.config.settings import settings
from src.utils.logger import setup_logger
import httpx
from datetime import datetime

class SMSProviderStrategy(ABC):
    """
    Abstract base class defining the interface for all SMS provider strategies.
    """

    def __init__(self,config:Dict[str,Any]) -> None:
        self.config = config
        self.circuit_breaker = CircuitBreaker(
            config.get("failure_threshold",settings.failure_threshold),
            config.get("reset_timeout",settings.reset_timeout)
        )
        self.logger = setup_logger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    async def send_sms(self,request:SMSRequest) -> SMSResponse:
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        pass

    def can_execute(self) -> bool:
        """
        Check if this provider can execute (circuit breaker is closed).
        """
        return self.circuit_breaker.can_execute()
    
    def record_success(self):
        """Record a successful operation with the circuit breaker."""
        self.circuit_breaker.record_success()

    def record_failure(self):
        """Record a failed operation with the circuit breaker."""
        self.circuit_breaker.record_failure()

    def get_circuit_breaker_status(self) -> Dict[str, Any]:
        """Get the current status of the circuit breaker."""
        return self.circuit_breaker.get_status()
    
    
        

class ArkeselStrategy(SMSProviderStrategy):
    """
    Strategy implementation for the Arkesel SMS provider.
    """

    def __init__(self) -> None:
        config = {
            "api_key": settings.arkesel_api_key,
            "base_url": settings.arkesel_api_url,
            "sender_id": settings.arkesel_sender_id,
            "failure_threshold": settings.failure_threshold,
            "reset_timeout": settings.reset_timeout,
        }
        super().__init__(config)

    def get_provider_name(self) -> str:
        return "arkesel"
    

    async def send_sms(self,request:SMSRequest) -> SMSResponse:
        """
        Send SMS via Arkesel API with Arkesel-specific implementation.
        """
        if not self.can_execute():
            raise Exception(f"Arkesel circuit breaker is open")
        
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "sender": self.config["sender_id"],
                    "message": request.message,
                    "recipients": [request.recipient],
                }
                headers = {"api-key": self.config["api_key"]}
                response = await client.post(
                    f"{self.config['base_url']}/api/v2/sms/send",
                    json=payload,
                    headers=headers,
                )

                response.raise_for_status()
                result = response.json()

                if result.get("status") == "success":
                    self.record_success()
                    return SMSResponse(
                        success=True,
                        message_id=result.get("message_id",""),
                        provider=self.get_provider_name(),
                        timestamp=datetime.now(),
                        error=None,
                    )
                else:
                    error_msg = result.get("message","Unknown Arkesel API error")
                    raise Exception(f"Arkesel API error: {error_msg}")
        except httpx.HTTPStatusError as e:
            self.record_failure()
            self.logger.error(f"Arkesel HTTP error: {e}")
            raise Exception(f"Arkesel HTTP error: {e}")
        except Exception as e:
            self.record_failure()
            self.logger.error(f"Arkesel API error: {e}")
            raise e
        


class MnotifyStrategy(SMSProviderStrategy):
    """
    Strategy implementation for the Mnotify SMS provider.
    """

    def __init__(self) -> None:
        config = {
            "api_key": settings.mnotify_api_key,
            "base_url": settings.mnotify_api_url,
            "sender_id": settings.mnotify_sender_id,
            "failure_threshold": settings.failure_threshold,
            "reset_timeout": settings.reset_timeout,
        }
        super().__init__(config)

    def get_provider_name(self) -> str:
        return "mnotify"
    

    async def send_sms(self,request:SMSRequest) -> SMSResponse:
        """
        Send SMS via Mnotify API with Mnotify-specific implementation.
        """
        if not self.can_execute():
            raise Exception(f"Mnotify circuit breaker is open")
        
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "to": request.recipient,
                    "message": request.message,
                    "sender": self.config["sender_id"],
                }
                headers = {"Content-Type": "application/json"}
                response = await client.post(
                    f"{self.config['base_url']}/api/sms/quick?key={self.config['api_key']}",
                    json=payload,
                    headers=headers,
                )

                response.raise_for_status()
                result = response.json()

                if result.get("status") == "success":
                    self.record_success()
                    return SMSResponse(
                        success=True,
                        message_id=result["summary"].get("_id"),
                        provider=self.get_provider_name(),
                        timestamp=datetime.now(),
                        error=None,
                    )
                else:
                    error_msg = result.get("message","Unknown Mnotify API error")
                    raise Exception(f"Mnotify API error: {error_msg}")
        except httpx.HTTPStatusError as e:
            self.record_failure()
            self.logger.error(f"Mnotify HTTP error: {e}")
            raise Exception(f"Mnotify HTTP error: {e}")
        except Exception as e:
            self.record_failure()
            self.logger.error(f"Mnotify API error: {e}")
            raise e
        

class SMSProviderFactory:
    """
    Factory class for creating SMS provider strategies.
    """

    _providers:Dict[str,type] = {
        "arkesel": ArkeselStrategy,
        "mnotify": MnotifyStrategy,
    }
    
    
    @classmethod
    def register_provider(cls,name:str,strategy_class:type):
        """
        Register a new provider strategy.
        """
        cls._providers[name] = strategy_class
    
    @classmethod
    def create_provider(cls,name:str) -> SMSProviderStrategy:
        """
        Create a provider strategy instance by name.
        """
        if name not in cls._providers:
            raise ValueError(f"Unknown provider: {name}")
        
        strategy_class = cls._providers[name]
        return strategy_class()
    

    @classmethod
    def get_available_providers(cls) -> list:
        """Get list of available provider names."""
        return list(cls._providers.keys())
    
    @classmethod
    def create_all_providers(cls) -> list:
        """
        Create instances of all registered providers.
        """
        return [cls.create_provider(name) for name in cls._providers.keys()]
    






    