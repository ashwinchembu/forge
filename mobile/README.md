# Forge Mobile Client

Starter types and API client for a future **React Native** or **Expo** app.

## Quick start (Expo)

```bash
npx create-expo-app forge-app
cd forge-app
# Copy mobile/api.ts and mobile/types.ts into your project
```

Point the client at your backend:

```typescript
import { ForgeAPI } from "./api";

// Local preview (no MongoDB required)
const api = new ForgeAPI({
  baseUrl: "http://localhost:8000",
  preview: true,
});

// Production (Render)
const api = new ForgeAPI({
  baseUrl: "https://your-app.onrender.com",
  preview: false,
  programStart: "2026-05-19",
});

const dashboard = await api.getDashboard();
```

## iOS Simulator / Android Emulator networking

| Target | `baseUrl` |
|--------|-----------|
| iOS Simulator | `http://localhost:8000` |
| Android Emulator | `http://10.0.2.2:8000` |
| Physical device (same Wi‑Fi) | `http://<your-mac-ip>:8000` |

## Screen → API mapping

| Screen | Method | Live endpoint |
|--------|--------|---------------|
| Dashboard | `getDashboard()` | `/api/analysis/today` |
| Today's Workout | `getWorkoutTargets(week)` | `/api/program/targets/{week}` |
| History | `getWorkouts()` | `/api/workouts` |
| Nutrition | `getNutrition()` | `/api/nutrition` |
| Recovery | `getRecovery()` | `/api/recovery` |
| Progress | `getBodyMetrics()` | `/api/body-metrics` |

Bootstrap metadata: `GET /api/mobile/config`

## CORS for Expo web

Add to backend `.env`:

```
CORS_ORIGINS=http://localhost:8081,http://localhost:19006
```

## Next steps for the app

1. Tab navigator with 5 screens matching the preview UI
2. Pull-to-refresh calling `sync/all` (optional admin action)
3. Secure storage for `programStart` date
4. Push notifications when daily score drops (future)
