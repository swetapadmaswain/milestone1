# Deploy Backend to Render - Step-by-Step Guide

## Overview
This guide helps you deploy the FastAPI backend to Render's free tier so your Streamlit Cloud app can connect to it.

---

## Step 1: Prepare Your Code

### 1.1 Ensure Files are Committed
Make sure these files are in your GitHub repo:
- `backend/requirements.txt` ✅
- `backend/app/main.py` ✅
- `render.yaml` (we just created this)

### 1.2 Push to GitHub
```bash
git add render.yaml DEPLOY_TO_RENDER.md
git commit -m "Add Render deployment configuration"
git push origin main
```

---

## Step 2: Create Render Account

### 2.1 Sign Up
1. Go to **https://render.com**
2. Click **"Get Started for Free"**
3. Choose **"Sign up with GitHub"** (easiest option)
4. Authorize Render to access your GitHub repositories

---

## Step 3: Deploy Using Blueprint (Easiest Method)

### 3.1 Create New Blueprint Instance
1. In Render dashboard, click **"New +"** button (top right)
2. Select **"Blueprint"**
3. Connect your GitHub account if not already connected
4. Find and select your repository: `swetapadmaswain/milestone1`
5. Click **"Connect"**

### 3.2 Configure Blueprint
Render will detect the `render.yaml` file and pre-fill settings:
- **Service Name**: `restaurant-reco-backend`
- **Runtime**: Python 3
- **Plan**: Free

Click **"Apply"** and then **"Create Blueprint"**

---

## Step 4: Set Environment Variables

⚠️ **CRITICAL STEP** - Without this, your backend won't work!

### 4.1 Add GROQ API Key
1. In Render dashboard, click your service `restaurant-reco-backend`
2. Go to **"Environment"** tab
3. Click **"Add Environment Variable"**
4. Add:
   - **Key**: `GROQ_API_KEY`
   - **Value**: `gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   *(Use your actual key from `backend/.env` - do NOT commit this key to git!)*
5. Click **"Save Changes"**

### 4.2 Verify Other Variables
These should already be set from `render.yaml`:
- `DEBUG=false`
- `HOST=0.0.0.0`
- `PORT=8000`
- `GROQ_MODEL=llama-3.1-8b-instant`

---

## Step 5: Deploy!

### 5.1 Manual Deploy (First Time)
1. Go to **"Manual Deploy"** dropdown (top right)
2. Select **"Deploy latest commit"**
3. Wait for build (2-5 minutes)

### 5.2 Monitor Build Logs
Watch the deploy logs for any errors:
```
==> Running build command...
pip install -r backend/requirements.txt
...
==> Running 'cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000'
```

### 5.3 Verify Deployment
1. Wait for status to change to **"Live"** (green)
2. Click the URL (e.g., `https://restaurant-reco-backend-xxxxx.onrender.com`)
3. You should see: `{"status": "healthy", ...}`

---

## Step 6: Test Your Backend

### 6.1 Health Check
Open in browser:
```
https://your-backend-url.onrender.com/health
```
Should return:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "llm_status": "available"
}
```

### 6.2 Test Recommendation API
Use curl or Postman:
```bash
curl -X POST https://your-backend-url.onrender.com/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "location": "whitefield",
    "budget": "medium",
    "preferred_cuisine": "",
    "min_rating": 3.5,
    "top_n": 3,
    "session_id": "test123"
  }'
```

---

## Step 7: Connect to Streamlit Cloud

### 7.1 Copy Backend URL
From Render dashboard, copy your service URL:
```
https://restaurant-reco-backend-xxxxx.onrender.com
```

### 7.2 Configure Streamlit Secrets
1. Go to https://share.streamlit.io
2. Click your app: `milestone1-finedine`
3. Go to **Settings** → **Secrets**
4. Add:
```toml
BACKEND_API_URL = "https://restaurant-reco-backend-xxxxx.onrender.com"
```
5. Click **Save**

### 7.3 Reboot Streamlit App
1. Click **☰ Menu** → **Reboot**
2. Wait 30 seconds
3. Open your app - should show **🟢 Backend Connected**

---

## Troubleshooting

### Problem: Build Fails
**Solution**: Check logs for missing dependencies. Common fixes:
```bash
# If pandas/numpy issues, add to requirements.txt
numpy<2.0
pandas==2.1.4
```

### Problem: "Backend Offline" in Streamlit
**Solution**: 
1. Check if Render service shows "Live"
2. Verify `BACKEND_API_URL` in Streamlit secrets (no trailing `/`)
3. Test backend health endpoint directly

### Problem: Timeout on First Request
**Solution**: Render free tier sleeps after 15 min. First request wakes it up (takes 30-60s). This is normal for free tier.

### Problem: CORS Errors
**Solution**: Backend already has CORS configured for all origins. If issues persist, check:
- Backend URL uses `https://` not `http://`
- No trailing slash in URL

### Problem: LLM Not Working
**Solution**: 
1. Verify `GROQ_API_KEY` is set in Render environment variables
2. Check backend logs for "llm_status: unavailable"
3. Test key validity: `curl -H "Authorization: Bearer YOUR_KEY" https://api.groq.com/openai/v1/models`

---

## Free Tier Limitations

| Limit | Value |
|-------|-------|
| **Sleep** | After 15 min inactivity |
| **Wake time** | 30-60 seconds |
| **Bandwidth** | 100 GB/month |
| **Build minutes** | 500 min/month |
| **Disk** | Ephemeral (data resets on deploy) |

**Note**: For production, upgrade to paid tier for always-on service.

---

## Success Checklist

- [ ] Render account created
- [ ] GitHub repo connected
- [ ] Blueprint deployed
- [ ] `GROQ_API_KEY` set in environment variables
- [ ] Backend shows "Live" status
- [ ] Health endpoint returns `healthy`
- [ ] `/recommend` endpoint returns restaurants
- [ ] Backend URL added to Streamlit secrets
- [ ] Streamlit app shows "🟢 Backend Connected"
- [ ] Search works in Streamlit app

---

## Next Steps

After successful deployment:
1. Share your Streamlit app URL with others!
2. Monitor usage in Render dashboard
3. Set up custom domain (optional)
4. Consider upgrading for better performance

**Your deployed URLs:**
- Backend: `https://restaurant-reco-backend-xxxxx.onrender.com`
- Frontend (Streamlit): `https://milestone1-finedine.streamlit.app/`
