# Forge — Mobile Web UI Spec

Build a single-page React app (or vanilla HTML/JS) that serves as the mobile frontend for a fitness tracking API. The app should feel like a native iOS app — dark theme, clean typography, smooth transitions, and full-screen on iPhone when added to home screen.

## API Base URL

All data comes from JSON endpoints. Use these preview endpoints (return static demo data, no auth needed):

| Endpoint | Returns |
|----------|---------|
| `GET /api/preview/dashboard` | Today's score, lifts, nutrition, recovery, recommendations |
| `GET /api/preview/workouts` | Recent workout objects |
| `GET /api/preview/nutrition` | Daily nutrition objects |
| `GET /api/preview/recovery` | Sleep, HRV, heart rate, steps |
| `GET /api/preview/body-metrics` | Weight + body fat history |
| `GET /api/preview/program/week/1` | Exercise targets for the week |
| `GET /api/sync/status` | Sync countdown + last sync time |
| `GET /api/program/schedule` | Weekly schedule (Mon-Sun) |

In production, swap `/api/preview/*` paths for the live equivalents (`/api/analysis/today`, `/api/workouts`, etc.). The mobile config endpoint `GET /api/mobile/config` maps every screen to both paths.

---

## Design System

### Theme (dark only)

| Token | Value | Usage |
|-------|-------|-------|
| `--bg` | `#0a0a0f` | App background |
| `--surface` | `#111118` | Card backgrounds |
| `--surface-2` | `#1a1a24` | Elevated elements, modals |
| `--border` | `#252535` | Subtle dividers |
| `--text` | `#f0f0f5` | Primary text |
| `--text-secondary` | `#8888a0` | Labels, captions |
| `--accent` | `#6c5ce7` | Primary buttons, active tab, score ring |
| `--green` | `#00d68f` | "Hit" status, positive deltas |
| `--yellow` | `#ffaa00` | "Close" status, warnings |
| `--red` | `#ff6b6b` | "Missed" status, negative deltas |

### Typography

- Font: `-apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", sans-serif`
- Large numbers (score): `2.5rem`, weight `700`
- Section headers: `0.7rem`, uppercase, `letter-spacing: 0.08em`, color `text-secondary`
- Body: `0.95rem`
- Small labels: `0.8rem`

### Spacing & Layout

- Full viewport height (`100dvh`), no scroll on the body
- Max width `480px` centered (add subtle border on desktop)
- Cards: `border-radius: 16px`, padding `16px`, `12px` gap between cards
- Tab bar: fixed to bottom, `64px` height, blurred background (`backdrop-filter: blur(16px)`)
- Content area scrolls independently, padding at bottom for tab bar + safe area
- iPhone safe areas: `env(safe-area-inset-top)` and `env(safe-area-inset-bottom)`

### PWA

- `<meta name="apple-mobile-web-app-capable" content="yes">`
- `<meta name="theme-color" content="#0a0a0f">`
- manifest.json with `"display": "standalone"`

---

## Screens (5 tabs)

### 1. Dashboard (Home)

The primary screen. Shows today's daily score and a summary of everything.

**Layout (top to bottom):**

1. **Score Ring** — large circular ring with the score (0-100) centered inside
   - Ring border color: `--accent` at 100%, lerp toward `--red` at 0%
   - Animate on load (count up from 0)
   - Below the number: small text "Daily Score"

2. **Phase Badge** — pill-shaped, e.g. "CUT · WEEK 1"
   - Background: `--accent`, white text, centered

3. **Today's Workout Card** — title "TODAY'S WORKOUT" or workout name
   - If training day: show each exercise as a row:
     - Left: exercise name (truncate the parenthetical, e.g. "Bench Press" not "Bench Press (Barbell)")
     - Right: actual weight + status badge
     - Status colors: green "HIT", yellow "CLOSE", red "MISSED"
   - If rest day: show "Rest Day — 30 min incline walk"

4. **Macros Card** — compact horizontal layout
   - Title: "NUTRITION"
   - 4 stats in a 2x2 grid or horizontal row:
     - Calories: `2085 / 2200` with a subtle progress bar underneath
     - Protein: `172g / 180g` with progress bar
     - Carbs: `148g`
     - Fat: `58g`
   - Color the delta: green if within 100 cal of target, yellow if 100-300 off, red if 300+

5. **Recovery Card** — horizontal stat row
   - Sleep hours, HRV (ms), Resting HR (bpm), Steps
   - Each stat: large number on top, small label below
   - Flag sleep < 7h in red

6. **Recommendations Card** — list of 1-3 text items
   - Each item: slightly muted color, left-aligned
   - Thin divider between items

**Data source:** `GET /api/preview/dashboard`

```json
{
  "date": "2026-05-18",
  "week": 1,
  "phase": "cut",
  "expected_workout": "Upper A",
  "score": 78,
  "workout": {
    "exercises": [
      {
        "exercise": "Bench Press (Barbell)",
        "target_weight": 215,
        "actual_weight": 215,
        "target_reps": "6-8",
        "actual_reps": [8, 7, 6, 6],
        "status": "hit",
        "volume_delta_pct": 2.1
      }
    ],
    "hit_rate": 0.67
  },
  "nutrition": {
    "calories": 2085,
    "target_calories": 2200,
    "protein_g": 172,
    "target_protein_g": 180,
    "carbs_g": 148,
    "fat_g": 58,
    "calorie_delta": -115,
    "protein_delta": -8
  },
  "recovery": {
    "sleep_hours": 7.4,
    "hrv_ms": 42.5,
    "resting_heart_rate": 54,
    "steps": 8420
  },
  "recommendations": [
    "Protein 172g is 8g below target. Prioritize protein in remaining meals.",
    "Incline DB Press was close — consider staying at 85 lbs next session."
  ]
}
```

---

### 2. Workout

Shows today's programmed exercises with target weights, sets, reps, and rest times.

**Layout:**

1. **Header card** — workout name + day (e.g. "Upper A — Monday")
2. **Exercise cards** — one card per exercise:
   - Exercise name (bold, `1rem`)
   - Row 1: Target weight (large, right-aligned)
   - Row 2: Sets × Reps | Rest time
   - Subtle accent left-border on each card for visual rhythm

**Data source:** `GET /api/preview/program/week/1`

Response shape:
```json
{
  "week": 1,
  "phase": { ... },
  "program": {
    "Upper A": {
      "Bench Press (Barbell)": {
        "sets": 4,
        "reps": "6-8",
        "weight": 215,
        "rest_seconds": 180
      }
    }
  }
}
```

Show all exercises in the day that matches today's weekday. Fall back to "Upper A" in preview.

---

### 3. Food (Nutrition)

Daily nutrition tracking + food logging shortcuts.

**Layout:**

1. **Calorie ring** — similar to score ring but for calories
   - Show `consumed / target` inside
   - Ring fills proportionally

2. **Macro breakdown** — 3 horizontal bars or a stacked bar chart:
   - Protein (green), Carbs (accent), Fat (yellow)
   - Each shows `Xg / Yg target`

3. **Quick actions** (if Telegram bot is set up):
   - "Snap a photo" → reminder to send to Telegram bot
   - "Scan barcode" → reminder to text the UPC to the bot

**Data source:** `GET /api/preview/nutrition`

```json
[{
  "_id": "preview-n1",
  "date": "2026-05-18T00:00:00",
  "calories": 2085,
  "protein_g": 172,
  "carbs_g": 148,
  "fat_g": 58,
  "fiber_g": 28
}]
```

Combine with dashboard nutrition for targets.

---

### 4. Recovery

Sleep and readiness metrics.

**Layout:**

1. **Sleep card** — large sleep hours number + horizontal bar showing sleep stages (deep / REM / light) stacked
   - Deep: dark blue, REM: purple/accent, Light: muted

2. **Stats grid** — 2x2 grid:
   - HRV (ms) — higher is better, show trend arrow if you have history
   - Resting HR (bpm) — lower is better
   - Steps — with subtle target line at 8,000
   - Readiness score (if available)

**Data source:** `GET /api/preview/recovery`

```json
[{
  "_id": "preview-r1",
  "date": "2026-05-18T00:00:00",
  "sleep": { "total_hours": 7.4, "deep_hours": 1.8, "rem_hours": 1.6 },
  "hrv_ms": 42.5,
  "resting_heart_rate": 54,
  "steps": 8420
}]
```

---

### 5. Progress

Weight + body composition over time.

**Layout:**

1. **Current stats card** — large numbers:
   - Current weight (lbs)
   - Body fat %
   - Week-over-week delta (green for loss during cut, red for gain)

2. **Chart** — simple line or area chart of weight over time
   - X-axis: dates
   - Y-axis: weight (lbs)
   - Show the last 30 days
   - Use `<canvas>` or a lightweight chart lib

3. **History list** — date + weight + body fat % per row (scrollable)

**Data source:** `GET /api/preview/body-metrics`

```json
[
  { "_id": "preview-b1", "date": "2026-05-18T00:00:00", "weight_lbs": 198.2, "body_fat_pct": 14.1 },
  { "_id": "preview-b2", "date": "2026-05-11T00:00:00", "weight_lbs": 199.0, "body_fat_pct": 14.3 }
]
```

---

## Header (persistent)

- Left: "Forge" (bold, `1.25rem`)
- Right: refresh button (↻ icon)
- Subtitle line: "Week 1 · Cut phase · Upper A" (from dashboard data)
- Sync status pill: "Updated 4:23 PM · next in 12m" (from `GET /api/sync/status`)

The sync status response:
```json
{
  "sync_interval_minutes": 15,
  "briefing_hours": [7, 13, 19],
  "telegram_configured": false,
  "last_sync": { "at": "2026-05-18T23:32:28Z", ... },
  "next_sync_at": "2026-05-18T23:47:28Z",
  "seconds_until_next": 896
}
```

---

## Tab Bar (persistent, fixed bottom)

| Tab | Icon | Label |
|-----|------|-------|
| Dashboard | chart icon | Home |
| Workout | dumbbell icon | Workout |
| Nutrition | utensils icon | Food |
| Recovery | moon/sleep icon | Recovery |
| Progress | trending-up icon | Progress |

- Use SVG icons or a lightweight icon set (Lucide, Heroicons)
- Active tab: `--accent` color
- Inactive: `--text-secondary`
- Touch targets: minimum `64px` height

---

## Interactions

- **Tab switching:** instant, no page reload
- **Pull to refresh:** on mobile, pulling down from top triggers `POST /api/sync/all` then reloads data
- **Auto-refresh:** reload data every 15 minutes (matches data sync schedule)
- **Visibility change:** reload data when user returns to the tab
- **Score animation:** count up from 0 to actual score on dashboard load
- **Smooth transitions:** fade or slide content when switching tabs (subtle, 200ms)

---

## File to replace

The output should be a single HTML file that replaces `app/static/preview.html`. The app is served at `GET /api/app` and `GET /api/preview` — both return this file.

Keep it as a single self-contained HTML file (inline CSS + JS, no build step) so it works on the FastAPI backend without any bundler.

If you use a chart library, load it from CDN (e.g. Chart.js via `<script src="https://cdn.jsdelivr.net/npm/chart.js">`).

---

## What NOT to include

- No authentication/login screen (public API for now)
- No food logging form (that goes through Telegram bot)
- No dark/light mode toggle (dark only)
- No settings screen
- No onboarding flow
