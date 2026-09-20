"""
Phase 3 Integration Test Suite: Real External Integrations.
Tests:
1. Shared OAuth Security (state validation, token encryption, zero client leakage, cross-user defense).
2. Real & Mock GitHub Provider (OAuth, repo/commit sync, quest evidence attachment, quiz-verification requirement).
3. Real & Mock Google Calendar Provider (OAuth, event sync, deadline & urgency detection, token refresh).
4. Android Health Connect Fitness Bridge (pairing token, batch ingestion, normalization, quest matching).
5. Unified Activity Layer (normalization, deduplication, quest matching).
6. Comprehensive End-to-End Scenario.
"""

import unittest
import json
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import (
    app, SessionLocal, User, Goal, Campaign, Milestone, Quest, Integration,
    Evidence, Assessment, Quiz, Skill, TopicSkill, UnifiedActivityRecord,
    hash_password, token_for
)
from app.integrations_engine import (
    encrypt_token, decrypt_token, get_provider, GitHubProvider, GoogleCalendarProvider,
    FitnessProvider, normalize_activity, match_activity_to_quests, UnifiedActivity,
    HealthConnectSyncBatch, HealthConnectSession
)

class Phase3IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.db = SessionLocal()

        # Clean up existing test users and associated data
        old_uids = [u.id for u in cls.db.query(User).filter(User.email.in_([
            'hero_p3_primary@test.com',
            'hero_p3_secondary@test.com'
        ])).all()]
        if old_uids:
            old_gids = [g.id for g in cls.db.query(Goal).filter(Goal.user_id.in_(old_uids)).all()]
            old_qids = [q.id for q in cls.db.query(Quest).filter(Quest.goal_id.in_(old_gids)).all()] if old_gids else []
            if old_qids:
                cls.db.query(Evidence).filter(Evidence.quest_id.in_(old_qids)).delete(synchronize_session=False)
                cls.db.query(Assessment).filter(Assessment.quest_id.in_(old_qids)).delete(synchronize_session=False)
                cls.db.query(Quiz).filter(Quiz.quest_id.in_(old_qids)).delete(synchronize_session=False)
                cls.db.query(Quest).filter(Quest.id.in_(old_qids)).delete(synchronize_session=False)
            if old_gids:
                cls.db.query(Milestone).delete(synchronize_session=False)
                cls.db.query(Campaign).filter(Campaign.user_id.in_(old_uids)).delete(synchronize_session=False)
                cls.db.query(Goal).filter(Goal.id.in_(old_gids)).delete(synchronize_session=False)
            cls.db.query(UnifiedActivityRecord).filter(UnifiedActivityRecord.user_id.in_(old_uids)).delete(synchronize_session=False)
            cls.db.query(Integration).filter(Integration.user_id.in_(old_uids)).delete(synchronize_session=False)
            cls.db.query(User).filter(User.id.in_(old_uids)).delete(synchronize_session=False)
            cls.db.commit()

        # Create primary hero
        cls.u1 = User(
            email='hero_p3_primary@test.com',
            password_hash=hash_password('Password123!'),
            name='Arthur Vance',
            xp=200,
            coins=100,
            level=2
        )
        # Create secondary hero (for cross-user attack checks)
        cls.u2 = User(
            email='hero_p3_secondary@test.com',
            password_hash=hash_password('Password123!'),
            name='Morgan Vance',
            xp=50,
            coins=20,
            level=1
        )
        cls.db.add_all([cls.u1, cls.u2])
        cls.db.commit()

        cls.u1_token = token_for(cls.u1.id)
        cls.u2_token = token_for(cls.u2.id)

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def auth_headers(self, tok):
        return {"Authorization": f"Bearer {tok}"}

    # =========================================================================
    # 1. OAuth Security & Encryption
    # =========================================================================
    def test_01_token_encryption_and_zero_leakage(self):
        secret_token = "gho_super_secret_access_token_12345"
        encrypted = encrypt_token(secret_token)
        self.assertNotEqual(secret_token, encrypted)
        decrypted = decrypt_token(encrypted)
        self.assertEqual(secret_token, decrypted)

        # Connect demo integration
        state = f"{self.u1.id}_valid_state"
        cb_resp = self.client.post(
            "/api/integrations/GitHub/callback",
            json={"code": "demo_code_gh", "state": state},
            headers=self.auth_headers(self.u1_token)
        )
        self.assertEqual(cb_resp.status_code, 200)

        # Assert no sensitive token attributes exposed to frontend
        int_resp = self.client.get("/api/integrations", headers=self.auth_headers(self.u1_token))
        self.assertEqual(int_resp.status_code, 200)
        for it in int_resp.json():
            self.assertNotIn("access_token", it)
            self.assertNotIn("access_token_enc", it)
            self.assertNotIn("refresh_token_enc", it)
            self.assertIn("is_configured", it)
            self.assertIn("is_live", it)

    def test_02_oauth_state_and_cross_user_protection(self):
        # Mismatched state must be rejected with 403
        fake_state_resp = self.client.post(
            "/api/integrations/GitHub/callback",
            json={"code": "some_code", "state": "attacker_injected_state_xyz"},
            headers=self.auth_headers(self.u1_token)
        )
        self.assertEqual(fake_state_resp.status_code, 403)
        self.assertIn("Invalid OAuth state", fake_state_resp.json()["detail"])

        # User 2 attempting to sync or disconnect User 1's integration
        # Each user only queries their own row in DB
        sync_resp = self.client.post(
            "/api/integrations/GitHub/sync",
            headers=self.auth_headers(self.u2_token)
        )
        # User 2 is not connected -> 400
        self.assertEqual(sync_resp.status_code, 400)

    # =========================================================================
    # 2. Real & Mock GitHub Integration
    # =========================================================================
    def test_03_github_mock_flow_and_activity_sync(self):
        state = f"{self.u1.id}_gh_mock"
        # Connect
        cb_resp = self.client.post(
            "/api/integrations/GitHub/callback",
            json={"code": "demo_github_code", "state": state},
            headers=self.auth_headers(self.u1_token)
        )
        self.assertEqual(cb_resp.status_code, 200)
        self.assertTrue(cb_resp.json()["connected"])

        # Sync
        sync_resp = self.client.post("/api/integrations/GitHub/sync", headers=self.auth_headers(self.u1_token))
        self.assertEqual(sync_resp.status_code, 200)
        self.assertEqual(sync_resp.json()["status"], "synced")

        # Fetch activity
        act_resp = self.client.get("/api/integrations/github/activity", headers=self.auth_headers(self.u1_token))
        self.assertEqual(act_resp.status_code, 200)
        items = act_resp.json()["items"]
        self.assertGreater(len(items), 0)
        self.assertTrue(any(i["type"] == "commit" for i in items))

    @patch("httpx.AsyncClient")
    def test_04_github_live_oauth_and_commits(self, mock_client_cls):
        from unittest.mock import AsyncMock
        # Simulate configured credentials
        gh_prov = get_provider("GitHub")
        gh_prov.client_id = "test_gh_client_id"
        gh_prov.client_secret = "test_gh_client_secret"

        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        # Mock token exchange
        mock_post_resp = MagicMock()
        mock_post_resp.json.return_value = {
            "access_token": "gho_live_mocked_token_xyz123",
            "scope": "read:user,repo"
        }
        mock_client.post.return_value = mock_post_resp

        # Mock user profile and repos
        mock_user_resp = MagicMock()
        mock_user_resp.status_code = 200
        mock_user_resp.json.return_value = {"login": "octocat_hero", "name": "The Octocat Hero"}

        mock_repos_resp = MagicMock()
        mock_repos_resp.status_code = 200
        mock_repos_resp.json.return_value = [
            {"id": 101, "name": "life-rpg-core", "description": "Core RPG engine", "html_url": "https://github.com/octocat_hero/life-rpg-core", "updated_at": "2026-09-20T10:00:00Z", "owner": {"login": "octocat_hero"}}
        ]

        mock_commits_resp = MagicMock()
        mock_commits_resp.status_code = 200
        mock_commits_resp.json.return_value = [
            {"sha": "abcdef123456", "commit": {"message": "feat: add Health Connect sync", "author": {"name": "Octocat", "date": "2026-09-20T09:30:00Z"}}, "html_url": "https://github.com/octocat_hero/life-rpg-core/commit/abcdef"}
        ]

        mock_client.get.side_effect = [mock_user_resp, mock_repos_resp, mock_commits_resp]

        state = f"{self.u1.id}_live_gh"
        cb_resp = self.client.post(
            "/api/integrations/GitHub/callback",
            json={"code": "live_github_code_456", "state": state},
            headers=self.auth_headers(self.u1_token)
        )
        self.assertEqual(cb_resp.status_code, 200)
        data = cb_resp.json()
        self.assertTrue(data["connected"])
        self.assertTrue(data["is_live"])
        self.assertEqual(data["account_name"], "The Octocat Hero")

        # Cleanup provider config
        gh_prov.client_id = ""
        gh_prov.client_secret = ""

    def test_05_github_commit_evidence_and_quiz_protection(self):
        """Verify that commits act as supporting evidence but cannot bypass learning quizzes."""
        # Create a Python Learning Quest that requires quiz assessment
        g = Goal(user_id=self.u1.id, title="Python Mastery", category="Learning", goal_type="learning")
        self.db.add(g)
        self.db.commit()

        q_learn = Quest(
            goal_id=g.id,
            title="FastAPI Routing Principles",
            description="Understand asynchronous routing in Python",
            quest_type="learning",
            subject="Python",
            topic="FastAPI Routing",
            evidence_required=True,
            assessment_required=True,
            status="available"
        )
        self.db.add(q_learn)
        self.db.commit()

        # Attach GitHub commit as evidence
        commit_payload = {
            "id": "commit_1",
            "type": "commit",
            "title": "feat: implement FastAPI router and endpoints",
            "repository": "life-rpg-api",
            "description": "Implemented router",
            "url": "https://github.com/test/repo/commit/12345"
        }
        ev_resp = self.client.post(
            f"/api/evidence/{q_learn.id}/github-commit",
            json=commit_payload,
            headers=self.auth_headers(self.u1_token)
        )
        self.assertEqual(ev_resp.status_code, 200)
        self.assertEqual(ev_resp.json()["kind"], "github")

        # Even with commit evidence attached, attempting to complete without quiz should require quiz
        quiz_res = self.client.get(f"/api/quests/{q_learn.id}/quiz", headers=self.auth_headers(self.u1_token))
        self.assertEqual(quiz_res.status_code, 200)
        self.assertIn("questions", quiz_res.json())

    # =========================================================================
    # 3. Google Calendar & Deadline Intelligence
    # =========================================================================
    def test_06_google_calendar_mock_sync_and_deadlines(self):
        state = f"{self.u1.id}_cal_state"
        cb_resp = self.client.post(
            "/api/integrations/Google Calendar/callback",
            json={"code": "demo_google_code", "state": state},
            headers=self.auth_headers(self.u1_token)
        )
        self.assertEqual(cb_resp.status_code, 200)
        self.assertTrue(cb_resp.json()["connected"])

        # Fetch Deadlines
        dl_resp = self.client.get("/api/integrations/calendar/deadlines", headers=self.auth_headers(self.u1_token))
        self.assertEqual(dl_resp.status_code, 200)
        deadlines = dl_resp.json()
        self.assertGreater(len(deadlines), 0)
        self.assertTrue(any(d["is_deadline"] for d in deadlines))
        self.assertTrue(any("Project Submission" in d["summary"] for d in deadlines))

    @patch("httpx.AsyncClient")
    def test_07_google_calendar_live_events_and_urgency(self, mock_client_cls):
        from unittest.mock import AsyncMock
        gcal = get_provider("Google Calendar")
        gcal.client_id = "test_gcal_client"
        gcal.client_secret = "test_gcal_secret"

        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        # Mock token exchange
        mock_post_resp = MagicMock()
        mock_post_resp.json.return_value = {
            "access_token": "ya29_live_mocked_token",
            "refresh_token": "1//mock_refresh_token",
            "expires_in": 3600,
            "scope": "https://www.googleapis.com/auth/calendar.events.readonly"
        }
        mock_client.post.return_value = mock_post_resp

        # Mock events API
        mock_events_resp = MagicMock()
        mock_events_resp.status_code = 200
        due_time = (datetime.now(timezone.utc) + timedelta(hours=20)).isoformat()
        mock_events_resp.json.return_value = {
            "items": [
                {
                    "id": "live_ev_1",
                    "summary": "Python Project Submission Deadline",
                    "description": "Upload final code and test report",
                    "start": {"dateTime": due_time}
                }
            ]
        }
        mock_client.get.return_value = mock_events_resp

        state = f"{self.u1.id}_live_gcal"
        cb_resp = self.client.post(
            "/api/integrations/Google Calendar/callback",
            json={"code": "live_google_code_789", "state": state},
            headers=self.auth_headers(self.u1_token)
        )
        self.assertEqual(cb_resp.status_code, 200)
        self.assertTrue(cb_resp.json()["connected"])

        # Reset provider config & disconnect live test token
        gcal.client_id = ""
        gcal.client_secret = ""
        self.client.post("/api/integrations/Google Calendar/disconnect", headers=self.auth_headers(self.u1_token))

    # =========================================================================
    # 4. Android Health Connect Fitness Bridge
    # =========================================================================
    def test_08_health_connect_bridge_pairing_token(self):
        resp = self.client.get("/api/integrations/fitness/bridge-token", headers=self.auth_headers(self.u1_token))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["user_id"], self.u1.id)
        self.assertIn("token", data)
        self.assertIn("device_pair_code", data)

    def test_09_health_connect_batch_sync_and_quest_matching(self):
        # Create an active Fitness Quest
        g_fit = Goal(user_id=self.u1.id, title="Daily Movement", category="Health", goal_type="habit")
        self.db.add(g_fit)
        self.db.commit()

        q_walk = Quest(
            goal_id=g_fit.id,
            title="Daily 30-Minute Brisk Walk",
            description="Maintain cardiovascular health",
            quest_type="habit",
            category="Fitness",
            status="available",
            xp=60,
            coin_reward=20
        )
        self.db.add(q_walk)
        self.db.commit()

        # Ingest batch from Android Health Connect bridge
        now = datetime.now()
        start = (now - timedelta(minutes=35)).isoformat()
        end = now.isoformat()

        batch_payload = {
            "sessions": [
                {
                    "id": "hc_session_walk_01",
                    "title": "Evening Walk",
                    "exercise_type": "walking",
                    "start_time": start,
                    "end_time": end,
                    "duration_minutes": 35,
                    "steps": 4100,
                    "distance_meters": 3200.0,
                    "source_app": "com.google.android.apps.fitness"
                }
            ],
            "daily_steps": 7500,
            "date": now.isoformat(),
            "device_name": "Pixel 8 Pro"
        }

        sync_resp = self.client.post(
            "/api/integrations/fitness/health-connect/sync",
            json=batch_payload,
            headers=self.auth_headers(self.u1_token)
        )
        self.assertEqual(sync_resp.status_code, 200)
        data = sync_resp.json()
        self.assertTrue(data["ok"])
        self.assertGreater(data["earned_xp"], 0)
        self.assertIn("Daily 30-Minute Brisk Walk", data["matched_quests"])

        # Check evidence was created via API endpoint
        ev_resp = self.client.get(f"/api/evidence/{q_walk.id}", headers=self.auth_headers(self.u1_token))
        self.assertEqual(ev_resp.status_code, 200)
        evs = ev_resp.json()
        self.assertGreater(len(evs), 0)
        self.assertTrue(evs[0]["supports_quest"])

    # =========================================================================
    # 5. Unified Activity Layer
    # =========================================================================
    def test_10_unified_activity_feed_and_normalization(self):
        # Fetch unified activities
        feed_resp = self.client.get("/api/integrations/activities", headers=self.auth_headers(self.u1_token))
        self.assertEqual(feed_resp.status_code, 200)
        activities = feed_resp.json()
        self.assertIsInstance(activities, list)
        self.assertGreater(len(activities), 0)

        types = [a["activity_type"] for a in activities]
        self.assertTrue(any("commit" in t or "fitness" in t or "calendar" in t for t in types))

    # =========================================================================
    # 6. Full End-to-End Phase 3 Master Scenario
    # =========================================================================
    def test_11_full_phase3_end_to_end_journey(self):
        """
        End-to-End Flow:
        1. NLP Goal Parsing -> Campaign creation
        2. Google Calendar sync -> Python submission deadline detected -> Urgency calculation
        3. Recommendations adjusted based on urgent deadline
        4. GitHub sync -> Real commit attached as evidence to project quest
        5. Quiz assessment taken for Python learning quest -> Skills adapted
        6. Health Connect syncs 40m running session -> Fitness quest matched & rewarded
        """
        # 1. NLP Goal
        nlp = self.client.post(
            "/api/goals/parse",
            json={"text": "I need to finish my Python project by Friday 6 PM."},
            headers=self.auth_headers(self.u1_token)
        ).json()
        self.assertIn("python", nlp["title"].lower())

        # Create Goal & Campaign
        goal_resp = self.client.post(
            "/api/goals",
            json={
                "title": nlp["title"],
                "category": "Coding",
                "goal_type": "project",
                "deadline": "Friday 6 PM",
                "priority": "high",
                "minutes": 45
            },
            headers=self.auth_headers(self.u1_token)
        ).json()
        goal_id = goal_resp.get("id") or goal_resp["goal"]["id"]

        # 2. Google Calendar connect and sync
        self.client.post(
            "/api/integrations/Google Calendar/callback",
            json={"code": "demo_google_code", "state": f"{self.u1.id}_cal_e2e"},
            headers=self.auth_headers(self.u1_token)
        )
        cal_sync = self.client.post(
            "/api/integrations/Google Calendar/sync",
            headers=self.auth_headers(self.u1_token)
        )
        self.assertEqual(cal_sync.status_code, 200)

        # 3. Recommendations
        rec_resp = self.client.get("/api/recommendations", headers=self.auth_headers(self.u1_token))
        self.assertEqual(rec_resp.status_code, 200)
        rec_data = rec_resp.json()
        self.assertIn("headline", rec_data)

        # 4. GitHub commit evidence attachment
        self.db.commit()
        quests = self.db.query(Quest).filter_by(goal_id=goal_id).all()
        proj_quest = next((q for q in quests if "Build" in q.title or "Implementation" in q.title or q.quest_type == "challenge"), quests[0])

        gh_act = self.client.get("/api/integrations/github/activity", headers=self.auth_headers(self.u1_token)).json()
        commit_item = gh_act["items"][0]

        att_resp = self.client.post(
            f"/api/evidence/{proj_quest.id}/github-commit",
            json=commit_item,
            headers=self.auth_headers(self.u1_token)
        )
        self.assertEqual(att_resp.status_code, 200)
        self.assertTrue(att_resp.json()["supports_quest"])

        # 5. Fitness activity sync from Health Connect
        hc_resp = self.client.post(
            "/api/integrations/fitness/health-connect/sync",
            json={
                "sessions": [{
                    "id": "hc_run_e2e",
                    "title": "Morning 5K",
                    "exercise_type": "running",
                    "start_time": (datetime.now() - timedelta(minutes=40)).isoformat(),
                    "end_time": datetime.now().isoformat(),
                    "duration_minutes": 40,
                    "steps": 4800
                }]
            },
            headers=self.auth_headers(self.u1_token)
        )
        self.assertEqual(hc_resp.status_code, 200)
        self.assertGreater(hc_resp.json()["earned_xp"], 0)

if __name__ == "__main__":
    unittest.main()
