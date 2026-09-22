# NOVAX-AI Deployment Guide (Vercel & Render)

This guide walks you through deploying **NOVAX-AI** to **Vercel** (Serverless) and **Render** (Cloud Web Service).

---

## 🚀 Option 1: Deploy on Render (Recommended for full web servers)

Render runs NOVAX-AI as a persistent cloud Python web service with background automation.

### Step-by-Step Instructions:

1. **Push your code to GitHub**:
   ```bash
   git add .
   git commit -m "Configure deployment for Render and Vercel"
   git push origin main
   ```

2. **Log in to Render**:
   - Go to [dashboard.render.com](https://dashboard.render.com/) and sign in with your GitHub account.

3. **Create a New Web Service**:
   - Click **New +** &rarr; **Web Service**.
   - Select your **NOVAX-AI** repository.

4. **Configure the Service**:
   - **Name**: `novax-ai`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py web`
   - **Instance Type**: `Free`

5. **Environment Variables** (Under *Environment Variables* section):
   - `HOST` = `0.0.0.0`
   - `PYTHON_VERSION` = `3.11.9`
   - *(Optional)* `OLLAMA_HOST` = `<your-remote-ollama-url>` (if using external Ollama)

6. **Deploy**:
   - Click **Create Web Service**.
   - Render will build and deploy your app, providing a live URL like `https://novax-ai.onrender.com`.

---

## ⚡ Option 2: Deploy on Vercel (Serverless)

Vercel provides serverless scaling and edge distribution for web applications.

### Step-by-Step Instructions:

1. **Push your code to GitHub**:
   ```bash
   git add .
   git commit -m "Configure deployment for Render and Vercel"
   git push origin main
   ```

2. **Log in to Vercel**:
   - Go to [vercel.com](https://vercel.com/) and sign in with GitHub.

3. **Import Project**:
   - Click **Add New...** &rarr; **Project**.
   - Select your **NOVAX-AI** repository.

4. **Framework Preset**:
   - Framework Preset: **Other**
   - Root Directory: `./`
   - Build & Output Settings: Default

5. **Deploy**:
   - Click **Deploy**.
   - Vercel automatically detects `vercel.json` and `api/index.py`, routing all web traffic and API endpoints to your serverless backend.
   - You will receive a live URL like `https://novax-ai.vercel.app`.

---

## ⚙️ Configuration Files Added

| File | Platform | Purpose |
|------|----------|---------|
| [api/index.py](file:///Users/sriramprasath/Documents/NOVAX-AI/api/index.py) | Vercel | Serverless Function entrypoint wrapping NOVAX Request Handler |
| [vercel.json](file:///Users/sriramprasath/Documents/NOVAX-AI/vercel.json) | Vercel | URL rewrites directing all routes to `api/index.py` |
| [render.yaml](file:///Users/sriramprasath/Documents/NOVAX-AI/render.yaml) | Render | Infrastructure blueprint for one-click deployment |
| [Procfile](file:///Users/sriramprasath/Documents/NOVAX-AI/Procfile) | Render / PaaS | Declares web worker process command (`python main.py web`) |
| [requirements.txt](file:///Users/sriramprasath/Documents/NOVAX-AI/requirements.txt) | Both | Dependencies for deployment builds |

---

## 🧪 Local Testing

To test the cloud-ready web server locally before deploying:
```bash
python3 main.py web
```
Open your browser at `http://127.0.0.1:8000`.
