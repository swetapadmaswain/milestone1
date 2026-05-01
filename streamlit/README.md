# Phase 5: Streamlit Deployment

Lightweight web interface for the Restaurant Recommendation System using Streamlit.

## ⚠️ Important: Backend Deployment Required

**Streamlit Cloud cannot access your local backend!** You must deploy your FastAPI backend to a cloud service first.

### Backend Deployment Options (Free Tiers)

1. **Render** (Recommended) - https://render.com
   - Free tier available
   - Easy FastAPI deployment
   - Automatic HTTPS

2. **Railway** - https://railway.app
   - Free tier available
   - Simple deployment

3. **Heroku** - https://heroku.com
   - Free tier available
   - Well-documented

4. **AWS/GCP/Azure** - Paid services

### Quick Start

#### Local Development

```bash
cd streamlit
pip install -r requirements.txt
streamlit run app.py
```

Access at: http://localhost:8501

The app will automatically connect to `http://localhost:8000` for local development.

#### Streamlit Cloud Deployment

1. **Deploy Backend First**
   - Follow one of the backend deployment options above
   - Get your backend URL (e.g., `https://your-backend.onrender.com`)

2. **Configure Secrets in Streamlit Cloud**
   - Go to your app dashboard: https://share.streamlit.io
   - Click **Settings** → **Secrets**
   - Add:
     ```
     BACKEND_API_URL = "https://your-backend-url.com"
     ```

3. **Deploy Streamlit App**
   - Connect your GitHub repo to Streamlit Cloud
   - The app will read the backend URL from secrets

### With Docker

```bash
cd streamlit
docker build -t restaurant-reco-streamlit .
docker run -p 8501:8501 -e BACKEND_API_URL=http://host.docker.internal:8000 restaurant-reco-streamlit
```

## Configuration

### Local Development (Environment Variable)
```bash
export BACKEND_API_URL="http://localhost:8000"
streamlit run app.py
```

### Streamlit Cloud (Secrets)
Set in Streamlit Cloud dashboard: **Settings** → **Secrets**
```toml
BACKEND_API_URL = "https://your-backend-url.com"
```

### Available Settings
- `BACKEND_API_URL` - FastAPI backend URL (default: http://localhost:8000)

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
