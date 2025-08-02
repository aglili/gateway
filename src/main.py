from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException, status

from src.config.settings import settings
from src.schema import SMSRequest, SMSResponse
from src.utils.logger import setup_logger
from src.utils.sms_orchestrator import get_sms_orchestrator, SMSOrchestrator    

logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("SMS Gateway with Circuit Breaker started")
    yield
    logger.info("SMS Gateway with Circuit Breaker stopped")


app = FastAPI(
    title=settings.application_name, version=settings.api_version, lifespan=lifespan
)


@app.post("/sms/send", response_model=SMSResponse)
async def send_sms(
    request: SMSRequest, sms_orchestrator: SMSOrchestrator = Depends(get_sms_orchestrator)
):
    try:
        response = await sms_orchestrator.send_sms(request)

        if not response.success:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=response.error
            )

        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send SMS: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@app.get("/health")
async def health_check(sms_orchestrator: SMSOrchestrator = Depends(get_sms_orchestrator)):
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "circuit_breaker_status": await sms_orchestrator.get_provider_status(),
    }


@app.get("/circuit-breaker-status")
async def circuit_breaker_status(sms_orchestrator: SMSOrchestrator = Depends(get_sms_orchestrator)):
    return await sms_orchestrator.get_provider_status()


@app.post("/circuit-breaker/reset")
async def reset_circuit_breaker(sms_orchestrator: SMSOrchestrator = Depends(get_sms_orchestrator)):
    await sms_orchestrator.reset_all_circuit_breakers()
    return {"status": "Circuit breakers reset"}
