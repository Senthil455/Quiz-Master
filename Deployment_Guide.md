# QuizMaster Deployment Guide

## Option 1: Deploy to Railway.app (Recommended)

### 1. Install Git and push to GitHub
```powershell
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/quizmaster.git
git push -u origin main
```

### 2. Create account on Railway.app
- Go to https://railway.app
- Sign up with GitHub
- Create a new project

### 3. Connect GitHub repo
- In Railway, select "New Project"
- Choose "Deploy from GitHub repo"
- Select your `quizmaster` repo
- Railway will auto-detect Flask

### 4. Add PostgreSQL
- In Railway project, click "Add Service"
- Select "PostgreSQL"
- Connect it (Railway sets `DATABASE_URL` automatically)

### 5. Set environment variables
In Railway project settings, add:
```
FLASK_ENV=production
SECRET_KEY=your_secret_key_here
```

### 6. Deploy
Railway auto-deploys on git push. Your app will be live at:
```
https://your-app-name.railway.app
```

---

## Option 2: Deploy to Render.com

Similar to Railway, but slightly different UI:
- https://render.com
- Connect GitHub repo
- Add PostgreSQL service
- Set environment variables
- Auto-deploys on push

---

## Option 3: Use Netlify + Backend Separation

If you want to use Netlify for the frontend:

### 1. Deploy Flask backend elsewhere (Railway/Render)
### 2. Deploy frontend to Netlify
- Separate HTML/CSS/JS to a `frontend/` folder
- Build static files
- Push to GitHub
- Connect to Netlify

This is more complex and requires frontend/backend separation.

---

## Environment Variables Needed

For any hosting platform:
```
DATABASE_URL=postgresql://postgres:4321@host:5432/quizdb
FLASK_ENV=production
FLASK_DEBUG=False
```

(Railway/Render auto-provide DATABASE_URL if you add PostgreSQL service)

---

## Local Testing Before Deploy

```powershell
.\.venv\Scripts\Activate.ps1
$env:FLASK_ENV = 'production'
python app.py
```

Then test at http://localhost:5000

---

## Troubleshooting

- **App not starting**: Check logs in railway/render dashboard
- **Database connection error**: Verify DATABASE_URL environment variable
- **Port issues**: Railway/Render assign a PORT env var; Flask needs to use `os.environ.get('PORT', 5000)`

---

## Recommended: Quick Deploy to Railway

1. Sign up: https://railway.app (use GitHub)
2. Create project → Connect GitHub repo
3. Add PostgreSQL service
4. Set env vars
5. Deploy

Takes about 5-10 minutes total.
