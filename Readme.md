# SMS Gateway with Circuit Breaker

A robust SMS gateway service built with FastAPI that supports multiple SMS providers with automatic failover and circuit breaker pattern implementation.

## Features

- **Multi-Provider Support**: Integrates with Arkesel and Mnotify SMS providers
- **Circuit Breaker Pattern**: Prevents cascading failures and improves system resilience
- **Automatic Failover**: Automatically switches between providers if one fails
- **Health Monitoring**: Built-in health checks and circuit breaker status monitoring
- **Async/Await**: Fully asynchronous implementation for high performance
- **RESTful API**: Clean REST API with automatic documentation
- **Environment Configuration**: Flexible configuration via environment variables

## Architecture

```
gateway/
├── src/
│   ├── config/
│   │   └── settings.py          # Configuration management
│   ├── utils/
│   │   ├── circuit_breaker.py   # Circuit breaker implementation
│   │   ├── enums.py            # Enums and constants
│   │   ├── logger.py           # Logging setup
│   │   └── sms_providers.py    # SMS provider implementations
│   ├── main.py                 # FastAPI application
│   └── schema.py               # Pydantic models
├── requirements.txt             # Python dependencies
└── README.md                   # This file
```

## Prerequisites

- Python 3.8+
- pip
- Virtual environment (recommended)

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd gateway
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```env
   # Arkesel Configuration
   ARKESEL_API_KEY=your_arkesel_api_key
   ARKESEL_API_URL=https://sms.arkesel.com
   ARKESEL_SENDER_ID=your_sender_id

   # Mnotify Configuration
   MNOTIFY_API_KEY=your_mnotify_api_key
   MNOTIFY_API_URL=https://api.mnotify.com
   MNOTIFY_SENDER_ID=your_sender_id

   ```

## Running the Application

### Development Mode
```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode
```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## API Endpoints

### Send SMS
**POST** `/sms/send`

Send an SMS message using the configured providers with automatic failover.

**Request Body:**
```json
{
  "recipient": "+233241234567",
  "message": "Hello from SMS Gateway!"
}
```

**Response:**
```json
{
  "success": true,
  "message_id": "A59CCB70-662D-45EF-9976-1EFAD249793D",
  "provider": "mnotify",
  "timestamp": "2024-01-15T10:30:00",
  "error": null
}
```

### Health Check
**GET** `/health`

Check the overall health of the service including circuit breaker status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00",
  "circuit_breaker_status": {
    "arkesel_status": {
      "state": "CLOSED",
      "failure_count": 0,
      "can_execute": true
    },
    "mnotify_status": {
      "state": "CLOSED",
      "failure_count": 0,
      "can_execute": true
    }
  }
}
```

### Circuit Breaker Status
**GET** `/circuit-breaker-status`

Get detailed circuit breaker status for all providers.

### Reset Circuit Breakers
**POST** `/circuit-breaker/reset`

Manually reset all circuit breakers to CLOSED state.

## Circuit Breaker Pattern

The application implements a circuit breaker pattern to improve system resilience:

- **CLOSED**: Normal operation, requests are allowed
- **OPEN**: Circuit is open, requests are blocked
- **HALF_OPEN**: Limited requests allowed to test if service is back

**Configuration:**
- `FAILURE_THRESHOLD`: Number of failures before opening circuit (default: 5)
- `RESET_TIMEOUT`: Time in seconds before attempting to close circuit (default: 30)

## SMS Providers

### Arkesel
- **API Endpoint**: `https://sms.arkesel.com/api/v2/sms/send`
- **Authentication**: API key in headers
- **Required Config**: `ARKESEL_API_KEY`, `ARKESEL_SENDER_ID`

### Mnotify
- **API Endpoint**: `https://api.mnotify.com/api/sms/quick`
- **Authentication**: API key in URL parameters
- **Required Config**: `MNOTIFY_API_KEY`, `MNOTIFY_SENDER_ID`

## Error Handling

The service implements comprehensive error handling:

1. **Provider Failover**: If one provider fails, automatically tries the next
2. **Circuit Breaker**: Prevents overwhelming failing providers
3. **Graceful Degradation**: Returns meaningful error messages
4. **Logging**: All errors are logged for monitoring

## Development

### Project Structure
```
src/
├── config/settings.py      # Configuration management
├── utils/
│   ├── circuit_breaker.py  # Circuit breaker implementation
│   ├── enums.py           # Enums and constants
│   ├── logger.py          # Logging setup
│   └── sms_providers.py   # SMS provider implementations
├── main.py                # FastAPI application
└── schema.py              # Pydantic models
```

### Adding New Providers

To add a new SMS provider:

1. Add configuration in `settings.py`
2. Implement provider method in `SMSProvider` class
3. Add provider to the providers list in `send_sms` method
4. Update circuit breaker initialization

### Testing

```bash
# Run with uvicorn for testing
uvicorn src.main:app --reload

# Test endpoints using curl
curl -X POST "http://localhost:8000/sms/send" \
     -H "Content-Type: application/json" \
     -d '{"recipient": "+233241234567", "message": "Test message"}'
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ARKESEL_API_KEY` | Arkesel API key | Required |
| `ARKESEL_API_URL` | Arkesel API URL | `https://sms.arkesel.com` |
| `ARKESEL_SENDER_ID` | Arkesel sender ID | Required |
| `MNOTIFY_API_KEY` | Mnotify API key | Required |
| `MNOTIFY_API_URL` | Mnotify API URL | `https://api.mnotify.com` |
| `MNOTIFY_SENDER_ID` | Mnotify sender ID | Required |
| `FAILURE_THRESHOLD` | Circuit breaker failure threshold | `5` |
| `RESET_TIMEOUT` | Circuit breaker reset timeout (seconds) | `30` |

