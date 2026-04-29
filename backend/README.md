# Restaurant Recommendation Backend API

A production-ready backend API for AI-powered restaurant recommendations with LLM integration, personalization, and comprehensive monitoring.

## Features

- **AI-Powered Recommendations**: Groq LLM integration for intelligent explanations
- **Personalization**: User profile management and learning from feedback
- **A/B Testing**: Built-in experimentation framework
- **Caching**: Multi-level caching with TTL support
- **Rate Limiting**: Configurable rate limiting per endpoint
- **Monitoring**: Comprehensive metrics and health checks
- **Security**: API key authentication and request validation
- **Scalability**: Async/await architecture with connection pooling

## Architecture

```
backend/
|-- app/
|   |-- core/           # Configuration and settings
|   |-- models/         # Database models and API schemas
|   |-- services/       # Business logic services
|   |-- middleware/     # Request/response middleware
|   |-- utils/          # Utility functions
|   `-- main.py         # FastAPI application entry point
|-- tests/              # Test suite
|-- storage/            # Data storage directories
|-- config/             # Configuration files
|-- docker/             # Docker configurations
`-- requirements.txt    # Python dependencies
```

## Quick Start

### Prerequisites

- Python 3.12+
- Docker and Docker Compose (optional)
- Groq API key (for LLM features)

### Local Development

1. **Clone and setup**:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Run the application**:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

4. **Access the API**:
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health
- Metrics: http://localhost:8000/metrics

### Docker Deployment

1. **Build and run with Docker Compose**:
```bash
docker-compose up -d
```

2. **Services available**:
- API: http://localhost:8000
- Grafana Dashboard: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090

## API Endpoints

### Core Endpoints

- **POST /api/v1/recommend** - Get personalized recommendations
- **POST /api/v1/feedback** - Submit user feedback
- **GET /api/v1/profile/{session_id}** - Get user profile

### Data Management

- **POST /api/v1/ingest** - Ingest and prepare restaurant data
- **GET /api/v1/catalog/info** - Get catalog statistics

### Monitoring & Health

- **GET /health** - Health check
- **GET /metrics** - System metrics
- **GET /admin/stats** - Administrative statistics

### Experimentation

- **GET /api/v1/experiments/assignments/{user_key}** - Get experiment assignments
- **POST /api/v1/experiments/track** - Track experiment events

## Usage Examples

### Get Recommendations

```bash
curl -X POST "http://localhost:8000/api/v1/recommend" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test_session_123",
    "location": "bangalore",
    "budget": "medium",
    "preferred_cuisine": "north indian",
    "min_rating": 4.0,
    "top_n": 5
  }'
```

### Submit Feedback

```bash
curl -X POST "http://localhost:8000/api/v1/feedback" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test_session_123",
    "restaurant_name": "Restaurant Name",
    "location": "bangalore",
    "cuisine": "north indian",
    "signal_type": "explicit",
    "signal_name": "like",
    "value": 1.0
  }'
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `false` | Enable debug mode |
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8000` | Server port |
| `GROQ_API_KEY` | - | Groq API key for LLM |
| `DATABASE_URL` | - | PostgreSQL connection string |
| `REDIS_URL` | - | Redis connection string |
| `RATE_LIMIT_PER_MIN` | `120` | Rate limit per minute |
| `CACHE_TTL_SECONDS` | `120` | Cache TTL in seconds |

### LLM Configuration

The system uses Groq API for generating restaurant explanations. Configure:

```python
GROQ_API_KEY="your-groq-api-key"
GROQ_MODEL="llama-3.1-8b-instant"
GROQ_TIMEOUT_SECONDS=8.0
GROQ_MAX_TOKENS=1000
```

## Services

### Recommendation Engine

Combines multiple scoring components:
- **Rule-based scoring** (rating, cost, cuisine match)
- **LLM scoring** (AI-powered evaluation)
- **Personalization scoring** (user preferences)

### Personalization Service

Learns from user behavior:
- Tracks explicit feedback (likes/dislikes)
- Captures implicit signals (clicks, dwell time)
- Applies time decay for preference evolution

### Experimentation Service

A/B testing framework:
- Configurable experiment variants
- Automatic user assignment
- Real-time metrics collection

### Caching Service

Multi-level caching:
- In-memory cache with TTL
- Optional Redis support for distributed deployments
- Cache hit/miss tracking

## Monitoring

### Metrics Collected

- Request latency and error rates
- LLM token usage and costs
- Cache performance
- User engagement metrics
- Experiment conversion rates

### Health Checks

- Database connectivity
- LLM service availability
- Cache service status
- Overall system health

## Development

### Running Tests

```bash
pytest tests/ -v --cov=app
```

### Code Quality

```bash
black app/
isort app/
mypy app/
```

### API Documentation

Interactive API documentation available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Deployment

### Production Deployment

1. **Environment Setup**:
   - Configure all environment variables
   - Set up PostgreSQL and Redis
   - Obtain Groq API key

2. **Docker Deployment**:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Health Monitoring**:
   - Monitor health endpoints
   - Set up alerts on metrics
   - Track error rates and latency

### Scaling Considerations

- **Horizontal Scaling**: Deploy multiple API instances behind load balancer
- **Database**: Use PostgreSQL with connection pooling
- **Cache**: Deploy Redis cluster for distributed caching
- **Monitoring**: Set up comprehensive monitoring and alerting

## Security

### Authentication

- API key authentication (optional)
- Request validation and sanitization
- Rate limiting per client

### Data Protection

- Input validation and sanitization
- SQL injection prevention
- Prompt injection protection
- PII handling compliance

## Troubleshooting

### Common Issues

1. **LLM Service Unavailable**:
   - Check Groq API key configuration
   - Verify network connectivity
   - Monitor token usage limits

2. **High Latency**:
   - Check cache hit rates
   - Monitor database query performance
   - Review LLM response times

3. **Memory Issues**:
   - Monitor cache size
   - Check for memory leaks
   - Review data ingestion volumes

### Logs

Structured logging with correlation IDs:
```bash
# View application logs
docker-compose logs -f backend

# View specific service logs
docker-compose logs -f postgres
```

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request

## License

This project is licensed under the MIT License.
