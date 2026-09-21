import unittest, json
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app, SessionLocal, User, Goal, Campaign, Milestone, Quest, Integration, Evidence, encrypt_token, hash_password, token_for

client = TestClient(app)
s = SessionLocal()
u = s.query(User).filter_by(email="github_progress_tester@test.com").first()
print("user:", u.id, u.email)

active_quest_rows = (
    s.query(Quest, Goal)
    .join(Goal, Quest.goal_id == Goal.id)
    .filter(Goal.user_id == u.id, Quest.status.in_(['available', 'in_progress']))
    .all()
)
print("active quests count:", len(active_quest_rows))
for q, g in active_quest_rows:
    print("Quest:", q.id, q.title, q.status, "Goal:", g.id, g.title)

token = token_for(u.id)

with patch("httpx.AsyncClient") as mock_client_cls:
    mock_client = AsyncMock()
    mock_client_cls.return_value.__aenter__.return_value = mock_client

    mock_repos_resp = MagicMock()
    mock_repos_resp.status_code = 200
    mock_repos_resp.json.return_value = [
        {
            "id": 9901,
            "name": "life-rpg-python-test",
            "description": "Python test repo",
            "html_url": "https://github.com/techy-ops/life-rpg-python-test",
            "updated_at": "2026-09-21T16:32:00Z",
            "owner": {"login": "techy-ops"}
        }
    ]

    commit_sha = "f179a2c610007d46a0fbeeb"
    mock_commits_resp = MagicMock()
    mock_commits_resp.status_code = 200
    mock_commits_resp.json.return_value = [
        {
            "sha": commit_sha,
            "commit": {
                "message": "Two sum testing updates",
                "author": {"name": "Krishna Keerthana", "date": "2026-09-21T16:30:00Z"}
            },
            "html_url": f"https://github.com/techy-ops/life-rpg-python-test/commit/{commit_sha}"
        }
    ]
    mock_client.get.side_effect = [mock_repos_resp, mock_commits_resp]

    resp = client.post("/api/integrations/GitHub/sync", headers={"Authorization": f"Bearer {token}"})
    print("Status code:", resp.status_code)
    print("Response JSON:", json.dumps(resp.json(), indent=2))
