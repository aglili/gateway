from typing import List, Optional,Dict,Any
from src.utils.sms_strategy import SMSProviderStrategy, SMSProviderFactory
from src.utils.logger import setup_logger
from src.schema import SMSRequest, SMSResponse
from datetime import datetime
import asyncio





class SMSOrchestrator:
    """
    Orchestrator for managing multiple SMS provider strategies.
    """

    def __init__(self,providers:Optional[List[SMSProviderStrategy]] = None):
        if providers is None:
            self.providers = SMSProviderFactory.create_all_providers()
        else:
            self.providers = providers

        self.logger = setup_logger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info(f"Initialized orchestrator with {len(self.providers)} providers")

    async def send_sms(self,request:SMSRequest) -> SMSResponse:
        """
        Send SMS using the best available provider with fallback logic.
        """

        last_error = None

        for provider in self.providers:
            provider_name = provider.get_provider_name()

            try:
                if not provider.can_execute():
                    self.logger.warning(f"Provider {provider_name} circuit breaker is open, skipping")
                    continue

                self.logger.info(f"Attempting to send SMS via {provider_name}")

                response = await provider.send_sms(request)

                if response.success:
                    self.logger.info(f"SMS sent successfully via {provider_name}")
                    return response
                else:
                    raise Exception(f"Provider {provider_name} returned success=False")
                
            except Exception as e:
                last_error = str(e)
                self.logger.error(f"Failed to send SMS via {provider_name}: {e}")
                continue

        error_msg = f"All SMS providers failed. Last error: {last_error}"
        self.logger.error(error_msg)

        return SMSResponse(
            success=False,
            message_id="",
            provider="none",
            timestamp=datetime.now(),
            error=error_msg,
        )
    

    async def send_sms_with_retry(self,request:SMSRequest,max_retries:int = 3) -> SMSResponse:
        """
        Send SMS with retry logic across all providers.
        """

        for attempt in range(max_retries + 1):
            if attempt > 0:
                wait_time = 2 ** (attempt - 1)
                self.logger.info(f"Retry attempt {attempt}/{max_retries} after {wait_time}s")
                await asyncio.sleep(wait_time)

            response = await self.send_sms(request)

            if response.success:
                return response
            
        error_msg = f"All retry attempts failed after {max_retries} retries"

        return SMSResponse(
            success=False,
            message_id="",
            provider="none",
            timestamp=datetime.now(),
            error=error_msg,
        )
    

    async def get_provider_status(self) -> Dict[str, Any]:
        """
        Get the status of all providers including circuit breaker states.
        """
        status = {}

        for provider in self.providers:
            provider_name = provider.get_provider_name()
            circuit_status = provider.get_circuit_breaker_status()

            status[provider_name] = {
                "available": provider.can_execute(),
                "circuit_breaker": circuit_status,
            }

        return status
    
    async def reset_all_circuit_breakers(self):
        """
        Reset circuit breakers for all providers."""
        for provider in self.providers:
            provider.circuit_breaker.reset()

        self.logger.info("Reset circuit breakers for all providers")

    def get_provider_names(self) -> List[str]:
        """Get list of provider names managed by this orchestrator."""
        return [provider.get_provider_name() for provider in self.providers]
    

    def add_provider(self,provider:SMSProviderStrategy):
        """
        Add a new provider to the orchestrator.
        """
        self.providers.append(provider)
        self.logger.info(f"Added provider: {provider.get_provider_name()}")

    def remove_provider(self,provider_name:str):
        """
        Remove a provider from the orchestrator."""
        self.providers = [p for p in self.providers if p.get_provider_name() != provider_name]
        self.logger.info(f"Removed provider: {provider_name}")


# Global orchestrator instance
# This follows the same pattern as the original implementation but with improved architecture
_orchestrator = SMSOrchestrator()

def get_sms_orchestrator() -> SMSOrchestrator:
    """Get the global SMS orchestrator instance."""
    return _orchestrator