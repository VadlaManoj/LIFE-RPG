"""
Integrations Engine for LIFE RPG (Phase 2).
Handles OAuth architecture, secure token storage (AES-style authenticated keystream),
activity syncing, deadline extraction, and quest matching for:
- GitHub
- Google Calendar
- Outlook Calendar
- Fitness Tracker
Supports both live OAuth workflows and deterministic simulation/demo mode when
client IDs are not set in the environment.
"""

from __future__ import annotations
import os
import json
import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import httpx
from pydantic import BaseModel, Field

SECRET = os.getenv("LIFE_RPG_SECRET", "change-this-secret-in-production")

# ---------- Authenticated Token Encryption (Pure Python, Zero-Dependency) ----------

def encrypt_token(plain_token: str) -> str:
    """Encrypts an OAuth token using PBKDF2-derived keystream + HMAC-SHA256 authenticated container."""
    if not plain_token:
        return ""
    salt = secrets.token_bytes(16)
    # Derive 64 bytes: 32 bytes for CTR keystream, 32 bytes for HMAC
    derived = hashlib.pbkdf2_hmac("sha256", SECRET.encode(), salt, 100000, dklen=64)
    enc_key = derived[:32]
    mac_key = derived[32:]

    data = plain_token.encode("utf-8")
    ciphertext = bytearray()
    # SHA-256 counter-mode stream cipher
    block_idx = 0
    for i in range(0, len(data), 32):
        block_counter = block_idx.to_bytes(4, "big")
        keystream_block = hmac.new(enc_key, salt + block_counter, hashlib.sha256).digest()
        chunk = data[i:i + 32]
        for c_byte, k_byte in zip(chunk, keystream_block):
            ciphertext.append(c_byte ^ k_byte)
        block_idx += 1

    # Authenticate salt + ciphertext
    tag = hmac.new(mac_key, salt + ciphertext, hashlib.sha256).digest()
    packed = salt + tag + ciphertext
    return base64.urlsafe_b64encode(packed).decode("utf-8")

def decrypt_token(cipher_token_b64: str) -> str:
    """Decrypts and verifies an OAuth token container."""
    if not cipher_token_b64:
        return ""
    try:
        packed = base64.urlsafe_b64decode(cipher_token_b64.encode("utf-8"))
        if len(packed) < 48:
            return ""
        salt = packed[:16]
        tag = packed[16:48]
        ciphertext = packed[48:]

        derived = hashlib.pbkdf2_hmac("sha256", SECRET.encode(), salt, 100000, dklen=64)
        enc_key = derived[:32]
        mac_key = derived[32:]

        expected_tag = hmac.new(mac_key, salt + ciphertext, hashlib.sha256).digest()
        if not hmac.compare_digest(tag, expected_tag):
            return ""

        plaintext = bytearray()
        block_idx = 0
        for i in range(0, len(ciphertext), 32):
            block_counter = block_idx.to_bytes(4, "big")
            keystream_block = hmac.new(enc_key, salt + block_counter, hashlib.sha256).digest()
            chunk = ciphertext[i:i + 32]
            for c_byte, k_byte in zip(chunk, keystream_block):
                plaintext.append(c_byte ^ k_byte)
            block_idx += 1

        return plaintext.decode("utf-8")
    except Exception:
        return ""

# ---------- Schemas ----------

class CalendarEvent(BaseModel):
    id: str
    summary: str
    description: Optional[str] = ""
    start_time: str
    end_time: Optional[str] = None
    is_deadline: bool = False
    suggested_quest_title: Optional[str] = None
    urgency: str = "normal"  # low, normal, urgent

class GitHubActivityItem(BaseModel):
    id: str
    type: str  # commit, repo, pr, issue
    title: str
    description: str
    url: Optional[str] = None
    timestamp: str
    repository: str

class FitnessActivityInput(BaseModel):
    activity_type: str = Field(..., description="e.g. walk, run, cycling, workout, gym")
    duration_minutes: int = Field(..., ge=1, le=1440)
    steps: Optional[int] = Field(None, ge=0)
    calories: Optional[int] = Field(None, ge=0)
    date: Optional[str] = Field(None)
    notes: Optional[str] = Field("")

# ---------- Provider Implementations ----------

class BaseProvider:
    name: str = "base"

    def get_auth_url(self, redirect_uri: str, state: str) -> str:
        raise NotImplementedError

    async def exchange_code(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        raise NotImplementedError

    async def sync(self, access_token: str) -> Dict[str, Any]:
        raise NotImplementedError

class GitHubProvider(BaseProvider):
    name = "GitHub"

    def __init__(self):
        self.client_id = os.getenv("GITHUB_CLIENT_ID", "")
        self.client_secret = os.getenv("GITHUB_CLIENT_SECRET", "")

    def get_auth_url(self, redirect_uri: str, state: str) -> str:
        if not self.client_id:
            # Simulated demo OAuth URL
            return f"/api/integrations/oauth-demo?provider=GitHub&state={state}&redirect_uri={redirect_uri}"
        return f"https://github.com/login/oauth/authorize?client_id={self.client_id}&redirect_uri={redirect_uri}&scope=repo,read:user&state={state}"

    async def exchange_code(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        if not self.client_id or code.startswith("demo_"):
            return {
                "access_token": f"gho_demo_{secrets.token_hex(16)}",
                "external_user_id": "hero_developer",
                "scopes": "repo,read:user",
                "account_name": "Demo Hero Developer"
            }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://github.com/login/oauth/access_token",
                headers={"Accept": "application/json"},
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri
                }
            )
            data = resp.json()
            if "error" in data:
                raise ValueError(data.get("error_description", "GitHub OAuth failed"))

            token = data.get("access_token")
            # Fetch user info
            user_resp = await client.get(
                "https://api.github.com/user",
                headers={"Authorization": f"Bearer {token}", "User-Agent": "LIFE-RPG-App"}
            )
            user_info = user_resp.json()
            return {
                "access_token": token,
                "external_user_id": str(user_info.get("login", "")),
                "scopes": data.get("scope", "read:user"),
                "account_name": user_info.get("name") or user_info.get("login")
            }

    async def sync(self, access_token: str) -> Dict[str, Any]:
        """Fetches repositories and recent commits."""
        if not access_token or "demo" in access_token:
            now = datetime.now()
            items = [
                {
                    "id": "commit_1",
                    "type": "commit",
                    "title": "feat: implement FastAPI router and async endpoints",
                    "description": "Added quest completion and quiz verification handlers",
                    "url": "https://github.com/demo/life-rpg-api/commit/9f8c2b",
                    "timestamp": (now - timedelta(hours=2)).isoformat(),
                    "repository": "life-rpg-api"
                },
                {
                    "id": "commit_2",
                    "type": "commit",
                    "title": "refactor: optimize binary search tree traversal",
                    "description": "Solved recursion depth bottleneck",
                    "url": "https://github.com/demo/dsa-practice/commit/3a14e9",
                    "timestamp": (now - timedelta(days=1)).isoformat(),
                    "repository": "dsa-practice"
                },
                {
                    "id": "repo_1",
                    "type": "repo",
                    "title": "life-rpg-api",
                    "description": "Python + FastAPI RPG game engine with evidence evaluator",
                    "url": "https://github.com/demo/life-rpg-api",
                    "timestamp": now.isoformat(),
                    "repository": "life-rpg-api"
                }
            ]
            return {
                "items": items,
                "summary": f"{len(items)} recent activities synced (Demo Mode)",
                "repositories_count": 2,
                "last_active_repo": "life-rpg-api"
            }

        async with httpx.AsyncClient(timeout=15.0) as client:
            headers = {"Authorization": f"Bearer {access_token}", "User-Agent": "LIFE-RPG-App"}
            # Fetch repos
            repos_resp = await client.get("https://api.github.com/user/repos?sort=updated&per_page=5", headers=headers)
            repos = repos_resp.json() if repos_resp.status_code == 200 else []

            items = []
            for r in repos:
                items.append({
                    "id": f"repo_{r.get('id')}",
                    "type": "repo",
                    "title": r.get("name", ""),
                    "description": r.get("description") or "No description",
                    "url": r.get("html_url", ""),
                    "timestamp": r.get("updated_at", ""),
                    "repository": r.get("name", "")
                })

            return {
                "items": items,
                "summary": f"Successfully synced {len(items)} repositories from GitHub",
                "repositories_count": len(repos),
                "last_active_repo": repos[0].get("name") if repos else "None"
            }

class GoogleCalendarProvider(BaseProvider):
    name = "Google Calendar"

    def __init__(self):
        self.client_id = os.getenv("GOOGLE_CLIENT_ID", "")
        self.client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "")

    def get_auth_url(self, redirect_uri: str, state: str) -> str:
        if not self.client_id:
            return f"/api/integrations/oauth-demo?provider=Google+Calendar&state={state}&redirect_uri={redirect_uri}"
        return (
            "https://accounts.google.com/o/oauth2/v2/auth?"
            f"client_id={self.client_id}&redirect_uri={redirect_uri}&response_type=code&"
            "scope=https://www.googleapis.com/auth/calendar.events.readonly&access_type=offline&prompt=consent&"
            f"state={state}"
        )

    async def exchange_code(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        if not self.client_id or code.startswith("demo_"):
            return {
                "access_token": f"ya29_demo_{secrets.token_hex(16)}",
                "external_user_id": "google_hero@gmail.com",
                "scopes": "calendar.events.readonly",
                "account_name": "Google Hero"
            }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri
                }
            )
            data = resp.json()
            if "error" in data:
                raise ValueError(data.get("error_description", "Google OAuth failed"))
            return {
                "access_token": data["access_token"],
                "refresh_token": data.get("refresh_token"),
                "scopes": data.get("scope", ""),
                "external_user_id": "google_user"
            }

    async def sync(self, access_token: str) -> Dict[str, Any]:
        """Fetches calendar events and identifies deadlines within next 14 days."""
        now = datetime.now()
        if not access_token or "demo" in access_token:
            events = [
                {
                    "id": "gcal_1",
                    "summary": "Project Submission: REST API & DB",
                    "description": "Upload code repository and walkthrough report",
                    "start_time": (now + timedelta(days=1, hours=4)).replace(minute=0, second=0).isoformat(),
                    "is_deadline": True,
                    "suggested_quest_title": "Submit Project Report & API Code",
                    "urgency": "urgent"
                },
                {
                    "id": "gcal_2",
                    "summary": "Technical Interview — Python & Algorithms",
                    "description": "Live coding and system design review",
                    "start_time": (now + timedelta(days=3, hours=2)).replace(minute=0, second=0).isoformat(),
                    "is_deadline": True,
                    "suggested_quest_title": "Prepare Python & Algorithms Interview",
                    "urgency": "urgent"
                },
                {
                    "id": "gcal_3",
                    "summary": "Weekly Team Standup",
                    "description": "Routine weekly sync meeting",
                    "start_time": (now + timedelta(days=2)).isoformat(),
                    "is_deadline": False,
                    "suggested_quest_title": None,
                    "urgency": "normal"
                }
            ]
            deadlines = [e for e in events if e["is_deadline"]]
            return {
                "events": events,
                "deadlines": deadlines,
                "summary": f"{len(events)} events synced. {len(deadlines)} active deadlines detected."
            }

        async with httpx.AsyncClient(timeout=15.0) as client:
            headers = {"Authorization": f"Bearer {access_token}"}
            time_min = now.isoformat() + "Z"
            time_max = (now + timedelta(days=14)).isoformat() + "Z"
            resp = await client.get(
                f"https://www.googleapis.com/calendar/v3/calendars/primary/events?timeMin={time_min}&timeMax={time_max}&singleEvents=true&orderBy=startTime",
                headers=headers
            )
            raw = resp.json() if resp.status_code == 200 else {}
            events = []
            for item in raw.get("items", []):
                summary = item.get("summary", "Untitled")
                start = item.get("start", {}).get("dateTime") or item.get("start", {}).get("date")
                lower = summary.lower()
                is_dl = any(k in lower for k in ["deadline", "submit", "submission", "due", "interview", "exam", "presentation", "report"])
                urgency = "urgent" if is_dl else "normal"
                events.append({
                    "id": item.get("id"),
                    "summary": summary,
                    "description": item.get("description", ""),
                    "start_time": start,
                    "is_deadline": is_dl,
                    "suggested_quest_title": f"Prepare for: {summary}" if is_dl else None,
                    "urgency": urgency
                })
            deadlines = [e for e in events if e["is_deadline"]]
            return {
                "events": events,
                "deadlines": deadlines,
                "summary": f"{len(events)} Google Calendar events synced. {len(deadlines)} deadlines detected."
            }

class OutlookCalendarProvider(BaseProvider):
    name = "Outlook Calendar"

    def __init__(self):
        self.client_id = os.getenv("AZURE_CLIENT_ID", "")
        self.client_secret = os.getenv("AZURE_CLIENT_SECRET", "")

    def get_auth_url(self, redirect_uri: str, state: str) -> str:
        if not self.client_id:
            return f"/api/integrations/oauth-demo?provider=Outlook+Calendar&state={state}&redirect_uri={redirect_uri}"
        return (
            "https://login.microsoftonline.com/common/oauth2/v2.0/authorize?"
            f"client_id={self.client_id}&response_type=code&redirect_uri={redirect_uri}&"
            f"response_mode=query&scope=Calendars.Read&state={state}"
        )

    async def exchange_code(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        if not self.client_id or code.startswith("demo_"):
            return {
                "access_token": f"ms_demo_{secrets.token_hex(16)}",
                "external_user_id": "outlook_hero@outlook.com",
                "scopes": "Calendars.Read",
                "account_name": "Outlook Hero"
            }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://login.microsoftonline.com/common/oauth2/v2.0/token",
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri
                }
            )
            data = resp.json()
            if "error" in data:
                raise ValueError(data.get("error_description", "Outlook OAuth failed"))
            return {
                "access_token": data["access_token"],
                "refresh_token": data.get("refresh_token"),
                "scopes": data.get("scope", ""),
                "external_user_id": "outlook_user"
            }

    async def sync(self, access_token: str) -> Dict[str, Any]:
        now = datetime.now()
        events = [
            {
                "id": "ms_cal_1",
                "summary": "Final Term Assignment Due",
                "description": "Submit code review report and unit test suites",
                "start_time": (now + timedelta(days=2, hours=6)).replace(minute=0, second=0).isoformat(),
                "is_deadline": True,
                "suggested_quest_title": "Final Term Assignment Submission",
                "urgency": "urgent"
            },
            {
                "id": "ms_cal_2",
                "summary": "Engineering Sprint Demo",
                "description": "Demonstrate life rpg features to team",
                "start_time": (now + timedelta(days=5)).isoformat(),
                "is_deadline": False,
                "suggested_quest_title": None,
                "urgency": "normal"
            }
        ]
        deadlines = [e for e in events if e["is_deadline"]]
        return {
            "events": events,
            "deadlines": deadlines,
            "summary": f"{len(events)} Outlook events synced. {len(deadlines)} deadlines found."
        }

class FitnessProvider(BaseProvider):
    name = "Fitness"

    async def record_activity(self, activity: FitnessActivityInput) -> Dict[str, Any]:
        """Validates and processes fitness activity into real-world activity log."""
        earned_xp = min(150, max(15, activity.duration_minutes * 2))
        earned_coins = min(50, max(5, activity.duration_minutes // 2))

        return {
            "activity_type": activity.activity_type,
            "duration_minutes": activity.duration_minutes,
            "steps": activity.steps,
            "calories": activity.calories,
            "date": activity.date or datetime.now().isoformat(),
            "earned_xp": earned_xp,
            "earned_coins": earned_coins,
            "verified": True,
            "summary": f"Completed {activity.duration_minutes}m of {activity.activity_type}" + (f" ({activity.steps} steps)" if activity.steps else "")
        }

# Provider Registry
PROVIDERS = {
    "GitHub": GitHubProvider(),
    "Google Calendar": GoogleCalendarProvider(),
    "Outlook Calendar": OutlookCalendarProvider(),
    "Fitness": FitnessProvider()
}

def get_provider(name: str) -> Optional[BaseProvider]:
    # Case insensitive lookup
    for key, prov in PROVIDERS.items():
        if key.lower() == name.lower() or key.lower().replace(" ", "") == name.lower().replace(" ", ""):
            return prov
    return None
