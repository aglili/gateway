from datetime import datetime

import httpx

from src.config.settings import settings
from src.schema import SMSRequest, SMSResponse
from src.utils.circuit_breaker import CircuitBreaker
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class SMSProvider:
    ARKESEL = "arkesel"
    MNOTIFY = "mnotify"

    def __init__(self) -> None:
        failure_threshold = settings.failure_threshold
        reset_timeout = settings.reset_timeout

        self.arkesel_circuit_breaker = CircuitBreaker(failure_threshold, reset_timeout)
        self.mnotify_circuit_breaker = CircuitBreaker(failure_threshold, reset_timeout)

        self.arkesel_config = {
            "api_key": settings.arkesel_api_key,
            "base_url": settings.arkesel_api_url,
            "sender_id": settings.arkesel_sender_id,
        }

        self.mnotify_config = {
            "api_key": settings.mnotify_api_key,
            "base_url": settings.mnotify_api_url,
            "sender_id": settings.mnotify_sender_id,
        }

        if not any(self.arkesel_config.values()) or not any(
            self.mnotify_config.values()
        ):
            logger.warning("Arkesel or Mnotify API key or base URL is not set")

    async def send_via_arkesel(self, request: SMSRequest) -> SMSResponse:
        if not self.arkesel_circuit_breaker.can_execute():
            raise Exception("Circuit breaker is open")

        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "sender": self.arkesel_config["sender_id"],
                    "message": request.message,
                    "recipients": [request.recipient],
                }

                headers = {"api-key": self.arkesel_config["api_key"]}

                response = await client.post(
                    f"{self.arkesel_config['base_url']}/api/v2/sms/send",
                    json=payload,
                    headers=headers,
                )

                response.raise_for_status()
                result = response.json()

                if result.get("status") == "success":
                    self.arkesel_circuit_breaker.record_success()
                    return SMSResponse(
                        success=True,
                        message_id=result.get("message_id", ""),
                        provider=SMSProvider.ARKESEL,
                        timestamp=datetime.now(),
                        error=None,
                    )
                else:
                    raise Exception(
                        f"Arkesel API returned an error: {result.get('message','Unknown error')}"
                    )
        except Exception as e:
            self.arkesel_circuit_breaker.record_failure()
            logger.error(f"Arkesel API error: {e}")
            raise e

    async def send_via_mnotify(self, request: SMSRequest) -> SMSResponse:
        if not self.mnotify_circuit_breaker.can_execute():
            raise Exception("Circuit breaker is open")

        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "to": request.recipient,
                    "message": request.message,
                    "sender": self.mnotify_config["sender_id"],
                }

                url = f"{self.mnotify_config['base_url']}/api/sms/quick?key={self.mnotify_config['api_key']}"

                headers = {"Content-Type": "application/json"}

                response = await client.post(url, json=payload, headers=headers)

                response.raise_for_status()
                result = response.json()

                if result.get("status") == "success":
                    self.mnotify_circuit_breaker.record_success()
                    return SMSResponse(
                        success=True,
                        message_id=result["summary"].get("_id"),
                        provider=SMSProvider.MNOTIFY,
                        timestamp=datetime.now(),
                        error=None,
                    )
                else:
                    raise Exception(
                        f"Mnotify API returned an error: {result.get('message','Unknown error')}"
                    )
        except Exception as e:
            self.mnotify_circuit_breaker.record_failure()
            logger.error(f"Mnotify API error: {e}")
            raise e

    async def send_sms(self, request: SMSRequest) -> SMSResponse:
        providers = [
            (self.send_via_arkesel, SMSProvider.ARKESEL),
            (self.send_via_mnotify, SMSProvider.MNOTIFY),
        ]

        for provider_func, provider_name in providers:
            try:
                logger.info(f"Sending SMS via {provider_name}")
                response = await provider_func(request)
                logger.info(f"SMS sent successfully via {provider_name}")
                return response
            except Exception as e:
                last_error = str(e)
                logger.error(f"Failed to send SMS via {provider_name}: {e}")
                continue
        return SMSResponse(
            success=False,
            message_id="",
            provider="none",
            timestamp=datetime.now(),
            error=f"All SMS providers failed: {last_error}",
        )

    async def circuit_breaker_status(self) -> dict:
        return {
            "arkesel_status": {
                "state": self.arkesel_circuit_breaker.state.value,
                "failure_count": self.arkesel_circuit_breaker.failure_count,
                "can_execute": self.arkesel_circuit_breaker.can_execute(),
            },
            "mnotify_status": {
                "state": self.mnotify_circuit_breaker.state.value,
                "failure_count": self.mnotify_circuit_breaker.failure_count,
                "can_execute": self.mnotify_circuit_breaker.can_execute(),
            },
        }

    async def reset_circuit_breakers(self):
        self.arkesel_circuit_breaker.reset()
        self.mnotify_circuit_breaker.reset()


sms_provider = SMSProvider()


def get_sms_provider():
    return sms_provider
