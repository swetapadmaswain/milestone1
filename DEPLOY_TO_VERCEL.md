# Deploy Frontend to Vercel - Step-by-Step Guide

## Overview
This guide helps you deploy the Next.js frontend to Vercel and connect it to your Render backend.

---

## Prerequisites

Before starting, ensure:
- [ ] Backend is deployed on Render (see DEPLOY_TO_RENDER.md)
- [ ] Backend URL is working (e.g., `https://your-backend.onrender.com`)
- [ ] GitHub repo is up to date

---

## Step 1: Create Vercel Account

### 1.1 Sign Up
1. Go to **https://vercel.com**
2. Click **"Sign Up"**
3. Choose **"Continue with GitHub"** (recommended)
4. Authorize Vercel to access your repositories

---

## Step 2: Deploy Frontend to Vercel

### 2.1 Import Project
1. In Vercel dashboard, click **"Add New..."** → **"Project"**
2. Find your GitHub repo: `swetapadmaswain/milestone1`
3. Click **"Import"**

### 2.2 Configure Project Settings
| Setting | Value |
|---------|-------|
| **Framework Preset** | Next.js |
| **Root Directory** | `frontend` |
| **Build Command** | `next build` (or leave default) |
| **Output Directory** | `.next` (or leave default) |
| **Install Command** | `npm install` (or leave default) |

### 2.3 Set Environment Variables
Click **"Environment Variables"** and add:

```
NEXT_PUBLIC_API_URL=https://your-backend.onrender.com
```

⚠️ **Important:** Replace with your actual Render backend URL!

### 2.4 Deploy
1. Click **"Deploy"**
2. Wait for build (2-3 minutes)
3. Vercel will provide a URL: `https://restaurant-reco-frontend-xxxxx.vercel.app`

---

## Step 3: Configure CORS on Backend (CRITICAL)

Your Render backend must accept requests from your Vercel frontend!

### 3.1 Update Render Environment Variables
1. Go to https://dashboard.render.com
2. Click your backend service
3. Go to **Environment** tab
4. Add/update:
   ```
   ALLOWED_ORIGINS=https://restaurant-reco-frontend-xxxxx.vercel.app
   ```

### 3.2 Update Backend CORS (if needed)
Check that `backend/app/main.py` has CORS configured:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

The backend already has CORS enabled for all origins, so this should work.

---

## Step 4: Verify Connection

### 4.1 Test Frontend URL
Open your Vercel URL:
```
https://restaurant-reco-frontend-xxxxx.vercel.app
```

### 4.2 Test Search
1. Enter location: `whitefield`
2. Select budget: `medium`
3. Click **"Get Recommendations"**
4. Should see restaurant results!

### 4.3 Check Browser Console
Open DevTools (F12) → Console:
- Look for CORS errors (red messages)
- Look for API connection errors

---

## Architecture After Deployment

```
┌─────────────────────────────────────────────────────────────┐
│  Vercel (Frontend)                                          │
│  https://restaurant-reco-frontend.vercel.app               │
│  (Next.js app - static export)                              │
└──────────────────┬────────────────────────────────────────────┘
                   │ API Calls (HTTP)
                   │ NEXT_PUBLIC_API_URL
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  Render (Backend)                                           │
│  https://restaurant-reco-backend.onrender.com              │
│  (FastAPI + Groq LLM)                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## Troubleshooting

### Problem: "Cannot connect to backend" or timeout

**Solution:**
1. Check `NEXT_PUBLIC_API_URL` is set correctly in Vercel
2. Verify backend is "Live" on Render
3. Test backend directly: `curl https://your-backend.onrender.com/health`

### Problem: CORS errors in browser console

**Solution:**
1. Backend CORS is already configured for `*`
2. If issues persist, add specific origin to Render env:
   ```
   ALLOWED_ORIGINS=https://your-vercel-url.vercel.app
   ```
3. Redeploy backend on Render

### Problem: Build fails on Vercel

**Solution:**
1. Check build logs in Vercel dashboard
2. Common fixes:
   ```bash
   # Update package.json with proper build script
   "scripts": {
     "build": "next build",
     "export": "next build"
   }
   ```
3. Ensure `frontend/tsconfig.json` is valid

### Problem: Static site shows 404 on refresh

**Solution:**
This is a Next.js static export issue. Update `next.config.js`:

```javascript
module.exports = {
  output: 'export',
  distDir: 'dist',
  images: {
    unoptimized: true
  }
}
```

---

## Alternative: Deploy as Static Site

If dynamic API doesn't work, deploy as static:

### 1. Update next.config.js
```javascript
module.exports = {
  output: 'export',
  distDir: 'dist',
  images: {
    unoptimized: true
  }
}
```

### 2. Build locally
```bash
cd frontend
npm install
npm run build
```

### 3. Deploy dist folder to Vercel
1. Drag `frontend/dist` folder to Vercel dashboard
2. Or use Vercel CLI: `vercel --prod`

⚠️ **Note:** Static export won't work for API calls - use this only for demo purposes without backend connection.

---

## Custom Domain (Optional)

### 1. Add Custom Domain in Vercel
1. Go to Vercel dashboard → Your project → **Domains**
2. Enter your domain: `dinesmart.yourdomain.com`
3. Follow DNS configuration instructions

### 2. Update Backend CORS
Add your custom domain to Render environment:
```
ALLOWED_ORIGINS=https://dinesmart.yourdomain.com,https://restaurant-reco-frontend-xxxxx.vercel.app
```

---

## Free Tier Limits (Vercel)

| Feature | Limit |
|---------|-------|
| **Builds** | 6,000 minutes/month |
| **Bandwidth** | 100 GB/month |
| **Serverless Functions** | 100 GB-hours |
| **Edge Requests** | 1 million/month |
| **Team Members** | 1 (personal) |

**Note:** Limits are generous for hobby projects. Upgrade to Pro for more.

---

## Success Checklist

- [ ] Vercel account created
- [ ] GitHub repo imported
- [ ] Root directory set to `frontend`
- [ ] `NEXT_PUBLIC_API_URL` set with Render backend URL
- [ ] Frontend deployed successfully
- [ ] Frontend URL loads without errors
- [ ] Search function works
- [ ] Restaurant recommendations display
- [ ] Backend health check passes

---

## Your Deployed URLs

After completion:
- **Frontend (Vercel):** `https://restaurant-reco-frontend-xxxxx.vercel.app`
- **Backend (Render):** `https://restaurant-reco-backend-xxxxx.onrender.com`
- **Streamlit (Cloud):** `https://milestone1-finedine.streamlit.app/`

**All three can work together!** 🎉

---

## Quick Reference Commands

```bash
# Test backend health
curl https://your-backend.onrender.com/health

# Test recommendation API
curl -X POST https://your-backend.onrender.com/recommend \
  -H "Content-Type: application/json" \
  -d '{"location":"whitefield","budget":"medium","min_rating":3.5,"top_n":3}'

# Local frontend test (before deploy)
cd frontend
npm install
npm run dev
```

---

## Need Help?

- **Vercel Docs:** https://vercel.com/docs
- **Next.js on Vercel:** https://nextjs.org/docs/deployment
- **Render CORS:** https://render.com/docs/cors
