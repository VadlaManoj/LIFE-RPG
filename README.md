# LIFE RPG — AI Life Campaign Engine

LIFE RPG turns a real-life goal into an adaptive RPG campaign: **goal → AI understanding → campaign → milestones → skills → quests → real-world action → evidence → AI evaluation → XP/coins/skill growth → adaptive difficulty → boss → campaign victory**.

## Included

- Authentication and onboarding
- Goal lifecycle: active / paused / completed / archived
- AI goal understanding with deterministic fallback
- AI campaign generator with milestones and final boss
- Real quest types: learning, practice, habit, build, challenge, social, boss, reinforcement
- Evidence: text, links, screenshots/files (8 MB limit)
- Adaptive difficulty and reinforcement quests
- Skill tree and mastery XP
- Hero/avatar/stats, coins, inventory and shop
- Streaks and daily missions
- Boss battles and campaign milestones
- Analytics, recap, weekly AI review and journal
- Achievements
- Community/accountability demo layer
- Integration connection states for GitHub, Google/Outlook Calendar, Focus Timer and Fitness
- Notifications and settings
- Responsive web UI
- Password hashing, signed sessions, ownership checks, upload validation and CORS

## Run

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite URL shown in the terminal.

## Optional OpenAI

Put the key **only in `backend/.env`**:

```env
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini
LIFE_RPG_SECRET=use-a-long-random-secret
```

The app still works without OpenAI using deterministic local intelligence. The API key is never sent to the browser.

## Integration note

The integration screens implement opt-in connection state and the data contracts needed by provider adapters. OAuth credentials for GitHub/Google/Outlook and fitness providers are deployment-specific, so this ZIP does not pretend those external authorizations are already configured.

## Clean database

This release uses `backend/liferpg_final.db`, separate from older LIFE RPG databases. Deleting that file resets the local database.
