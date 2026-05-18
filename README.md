# Forge

Your personal fitness intelligence backend. Forge pulls data from three sources (Hevy for lifting, MyFitnessPal for nutrition via Apple Health, and Oura for recovery), stores it in MongoDB, and runs an analysis engine that compares your real performance against a 12-week hypertrophy program with week-by-week weight targets.

## What It Does

**Every hour**, Health Auto Export pushes your Apple Health data (calories, macros, sleep, HRV, heart rate, steps, weight) to Forge's webhook endpoint. This captures everything MFP and Oura write to Apple Health automatically.

**Every 6 hours**, Forge pulls your latest workouts from Hevy's API, including every exercise, set, rep, and weight.

**On demand**, you can upload a MFP CSV export for detailed per-food breakdowns, or hit `/api/sync/all` to force a full refresh.

**The analysis engine** then takes all of this and compares it against your programmed targets:

- Did you hit your target weight on bench this week? By how many reps?
- Are you eating enough protein? How far off are you?
- Did you sleep 7+ hours? What's your HRV trend?
- Are you on track for your cut? Bulk? Reverse diet?
- What should you adjust tomorrow?

Every day gets a score (0-100) based on workout adherence, nutrition compliance, and recovery quality. Every exercise gets tagged as "hit", "close", or "missed" against the target weight for that specific week of the program.

## Architecture

```
iPhone
  |
  |-- MyFitnessPal (food logging)
  |       |
  |       v
  |   Apple Health  <----  Oura Ring (sleep, HRV, HR)
  |       |
  |       v
  |   Health Auto Export app
  |       |
  |       | POST /api/webhook/health-auto-export (hourly)
  |       v
  |   +-----------+       +-------------+
  |   |   Forge   | <---> |  MongoDB    |
  |   |  (FastAPI)|       |  (Atlas)    |
  |   +-----------+       +-------------+
  |       ^
  |       | Hevy API (auto every 6h)
  |       |
  |-- Hevy (workout tracking, Pro required)
```

## Setup Guide

### 1. MongoDB Atlas (Free Tier)

1. Go to mongodb.com/atlas and create a free account
2. Create a FREE M0 cluster (pick AWS us-east-1 to match Render)
3. Create a database user:
   - Database Access > Add New Database User
   - Password auth, username: `forgeadmin`, set a strong password
   - Privileges: Read and write to any database
4. Allow network access:
   - Network Access > Add IP Address > Allow Access from Anywhere (0.0.0.0/0)
   - Required for Render's dynamic IPs
5. Get your connection string:
   - Database > Connect > Drivers
   - Copy the string, replace `<password>` with your actual password
   - Add database name: `mongodb+srv://forgeadmin:PASS@cluster0.xxxxx.mongodb.net/forge`

### 2. Deploy to Render

1. Push this repo to GitHub (`.env` is gitignored, your keys are safe)
2. Go to render.com > New > Web Service > connect your GitHub repo
3. Configure:
   - Name: `forge`
   - Runtime: Python
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Instance Type: Free
4. Add environment variables:
   - `MONGO_URI` = your Atlas connection string
   - `MONGO_DB` = forge
   - `HEVY_API_KEY` = your Hevy Pro API key (from hevy.com/settings?developer)
   - `OURA_ACCESS_TOKEN` = your Oura token (from cloud.ouraring.com/personal-access-tokens)
   - `WEBHOOK_SECRET` = any secret string (e.g. `forge_webhook_2026`)
5. Deploy and wait for build
6. Visit `https://forge-xxxx.onrender.com/docs` to confirm

### 3. Set Up Health Auto Export (iPhone)

1. Download Health Auto Export from App Store (~$3, Premium required for automations)
2. Make sure MFP and Oura are syncing to Apple Health:
   - MFP: More > Apps & Devices > Health App > Connect
   - Oura: Settings > Apple Health > Enable all
3. Open Health Auto Export > Automations > New Automation > REST API
4. Configure:
   - URL: `https://your-render-app.onrender.com/api/webhook/health-auto-export`
   - Header: `Authorization: Bearer forge_webhook_2026`
   - Metrics: dietary_energy, dietary_protein, dietary_carbohydrates, dietary_fat_total, dietary_fiber, sleep_analysis, heart_rate_variability, resting_heart_rate, step_count, body_mass, body_fat_percentage
   - Format: JSON
   - Frequency: Every 1 hour
   - Batch Requests: ON
5. Enable and tap Sync Now to test

### 4. Verify

1. `POST /api/sync/all` - syncs Hevy + Oura
2. `GET /api/analysis/today?program_start=2026-05-19` - today's analysis
3. Check Health Auto Export automation history for successful webhooks

## API Endpoints

### Ingestion
- `POST /api/webhook/health-auto-export` - Health Auto Export hourly webhook
- `POST /api/sync/hevy` - manual Hevy pull (also auto every 6h)
- `POST /api/sync/oura` - manual Oura pull (also auto every 6h)
- `POST /api/sync/all` - sync everything
- `POST /api/upload/mfp-csv` - upload MFP CSV for food-level detail

### Analysis
- `GET /api/analysis/today?program_start=YYYY-MM-DD` - daily score + recs
- `GET /api/analysis/day/{date}?program_start=YYYY-MM-DD` - specific day
- `GET /api/analysis/week/{week_num}?program_start=YYYY-MM-DD` - weekly summary

### Data
- `GET /api/workouts?days=7` - recent workouts
- `GET /api/nutrition?days=7` - daily nutrition
- `GET /api/recovery?days=7` - sleep, HRV, HR
- `GET /api/body-metrics?days=30` - weight + body comp

### Program
- `GET /api/program/targets/{week}` - exercise targets for a given week
- `GET /api/program/schedule` - weekly schedule

## Mobile App

This is the API layer for a future React Native or Flutter app. Screen mapping:
- Dashboard: `/api/analysis/today`
- Today's Workout: `/api/program/targets/{week}`
- History: `/api/workouts`
- Nutrition: `/api/nutrition`
- Progress: `/api/body-metrics`
- Recovery: `/api/recovery`

## Notes

- Rotate API keys if you ever shared them in chat or committed them
- `.env` is gitignored and should never be committed
- Render free tier sleeps after 15 min idle. Health Auto Export retries automatically.
- Program targets live in `app/services/analysis_service.py`. Edit the PROGRAM dict to change exercises or progression.
