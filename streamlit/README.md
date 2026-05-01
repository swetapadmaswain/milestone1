# Phase 5: Streamlit Deployment

Lightweight web interface for the Restaurant Recommendation System using Streamlit.

## Quick Start

### Local Development

```bash
cd streamlit
pip install -r requirements.txt
streamlit run app.py
```

Access at: http://localhost:8501

### With Docker

```bash
cd streamlit
docker build -t restaurant-reco-streamlit .
docker run -p 8501:8501 -e BACKEND_API_URL=http://host.docker.internal:8000 restaurant-reco-streamlit
```

## Configuration

Set environment variables:

- `BACKEND_API_URL` - FastAPI backend URL (default: http://localhost:8000)
- `STREAMLIT_PORT` - UI port (default: 8501)

## Features

- ✅ Interactive search form (location, budget, cuisine, rating)
- ✅ AI-generated restaurant recommendations
- ✅ Expandable restaurant cards with explanations
- ✅ Feedback collection (like/dislike/favorite)
- ✅ Mobile responsive design
- ✅ Backend health check indicator
- ✅ Session management

## Architecture

```
┌─────────────────┐      HTTP POST      ┌─────────────────┐
│  Streamlit UI   │  ─────────────────>  │  FastAPI Backend│
│   (Port 8501)   │    /recommend        │   (Port 8000)   │
└─────────────────┘                      └─────────────────┘
```

## Deployment Options

1. **Streamlit Cloud** - Connect GitHub repo to streamlit.io
2. **Heroku** - Use container deployment
3. **AWS/GCP/Azure** - VM or container hosting
4. **Self-hosted** - Any server with Docker

## File Structure

```
streamlit/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
├── Dockerfile         # Container configuration
└── README.md          # This file
```

## Notes

- Ensure backend is running before starting Streamlit
- Location names should match dataset (e.g., "whitefield", "btm", "hsr")
- Backend URL can be configured via environment variable
