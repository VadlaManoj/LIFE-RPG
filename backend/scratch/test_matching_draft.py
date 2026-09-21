import re
from typing import List, Dict, Any, Optional

class DummyActivity:
    def __init__(self, activity_type: str, title: str, description: str, metadata: dict):
        self.activity_type = activity_type
        self.title = title
        self.description = description
        self.metadata = metadata

def tokenize(text: str) -> List[str]:
    text_clean = re.sub(r'[-_./\s]+', ' ', (text or '').lower())
    words = re.findall(r'\b[a-z0-9]{2,}\b', text_clean)
    stop = {'the', 'and', 'for', 'with', 'from', 'this', 'that', 'into', 'your', 'have', 'action', 'quest', 'complete', 'toward', 'small', 'repeatable'}
    return [w for w in words if w not in stop]

def match_activity_to_quests(
    activity: DummyActivity,
    quests: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    if not quests:
        return None

    act_type = activity.activity_type
    act_title_lower = (activity.title or "").lower()
    act_meta = activity.metadata or {}

    # 1. Fitness matching
    if act_type == "fitness_activity":
        fit_kind = str(act_meta.get("activity_type", "")).lower()
        for q in quests:
            q_cat = str(q.get("category", "")).lower()
            q_type = str(q.get("quest_type", "")).lower()
            q_title = str(q.get("title", "")).lower()
            if q.get("assessment_required") or q_type == "learning" or q_cat in ("learning", "coding", "career"):
                continue
            if q_cat in ("fitness", "health", "wellness") or q_type == "habit" or fit_kind in q_title or any(w in q_title for w in ["walk", "run", "workout", "gym", "cardio", "swim", "cycling", "steps"]):
                return q

    # 2. GitHub commit / repository matching
    elif act_type in ("github_commit", "github_repository"):
        raw_repo = str(act_meta.get("repository", "")).lower()
        repo_clean = re.sub(r'[-_./\s]+', ' ', raw_repo)
        repo_tokens = set(tokenize(raw_repo))
        commit_tokens = set(tokenize(act_title_lower))
        commit_words_longer = {w for w in commit_tokens if len(w) >= 3 and w not in ('feat', 'fix', 'test', 'update', 'add', 'refactor', 'changes', 'commit', 'code')}

        # Filter eligible quests for coding/projects/engineering
        eligible = []
        for q in quests:
            q_cat = str(q.get("category", "")).lower()
            q_type = str(q.get("quest_type", "")).lower()
            q_skill = str(q.get("skill", "")).lower()
            q_subject = str(q.get("subject", "")).lower()
            goal_cat = str(q.get("goal_category", "")).lower()
            goal_type = str(q.get("goal_type", "")).lower()

            # Disallow non-engineering domains
            if q_cat in ("fitness", "health", "wellness", "finance", "relationships") or q_skill in ("fitness", "health"):
                continue

            # Must be linked to code/project/learning/technical activity
            is_coding_domain = (
                q_cat in ("coding", "projects", "learning", "career", "personal") or
                goal_cat in ("coding", "projects", "learning", "career", "personal")
            )
            is_coding_skill = (
                any(k in q_skill for k in ["coding", "project", "python", "dsa", "software", "dev", "engineer", "fastapi", "web", "api"]) or
                any(k in q_subject for k in ["python", "dsa", "coding"]) or
                goal_type in ("project", "learning") or
                q_type in ("build", "project", "challenge", "practice", "habit", "boss", "learning")
            )
            if is_coding_domain and is_coding_skill:
                eligible.append(q)

        if not eligible:
            return None

        if act_type == "github_commit":
            best_match = None
            best_score = 0

            for q in eligible:
                score = 0
                q_title = str(q.get("title", "")).lower()
                q_desc = str(q.get("description", "")).lower()
                goal_title = str(q.get("goal_title", "")).lower()
                q_skill = str(q.get("skill", "")).lower()
                q_subject = str(q.get("subject", "")).lower()
                q_topic = str(q.get("topic", "")).lower()

                q_title_tokens = set(tokenize(q_title))
                q_desc_tokens = set(tokenize(q_desc))
                goal_tokens = set(tokenize(goal_title))
                skill_tokens = set(tokenize(f"{q_skill} {q_subject} {q_topic}"))

                quest_all_tokens = q_title_tokens | q_desc_tokens | goal_tokens | skill_tokens

                # Check repo match
                repo_in_text = bool(
                    raw_repo and (raw_repo in q_title or raw_repo in q_desc or raw_repo in goal_title)
                ) or bool(
                    repo_clean and (repo_clean in q_title or repo_clean in q_desc or repo_clean in goal_title)
                )

                # Meaningful repo token overlap (e.g. 'python', 'api', 'two', 'sum', 'fastapi', 'rpg')
                meaningful_repo_tokens = {w for w in repo_tokens if w not in ('the', 'test', 'demo', 'app', 'new')}
                repo_token_overlap = meaningful_repo_tokens & quest_all_tokens

                # Check commit keyword overlap
                # Meaningful commit token overlap with quest/goal
                overlap_title = commit_tokens & q_title_tokens
                overlap_desc = commit_tokens & q_desc_tokens
                overlap_goal = commit_tokens & goal_tokens
                overlap_skill = commit_tokens & skill_tokens
                all_keyword_overlap = commit_words_longer & quest_all_tokens

                # Direct task match
                if repo_in_text and (overlap_title or overlap_goal or all_keyword_overlap):
                    score += 10
                elif repo_token_overlap and (overlap_title or overlap_goal or all_keyword_overlap):
                    score += 7
                elif all_keyword_overlap:
                    # Domain-specific word overlap (e.g. 'router', 'auth', 'two', 'sum', 'graph')
                    score += 5 + len(all_keyword_overlap)
                elif (overlap_title or overlap_goal):
                    score += 4
                elif repo_token_overlap and any(w in act_title_lower for w in ["api", "router", "endpoint", "feat", "fix", "crud", "test", "build", "refactor", "changes", "update"]):
                    # Engineering action in related repo
                    score += 3

                # Prefer active coding/project quests over generic or assessment-required when committing real code
                if not q.get("assessment_required") and q.get("quest_type") in ("build", "project", "challenge", "practice", "habit"):
                    score += 1

                if score > best_score:
                    best_score = score
                    best_match = q

            if best_score >= 3:
                return best_match

        elif act_type == "github_repository":
            for q in eligible:
                q_title = str(q.get("title", "")).lower()
                q_desc = str(q.get("description", "")).lower()
                goal_title = str(q.get("goal_title", "")).lower()
                if raw_repo and (raw_repo in q_title or raw_repo in q_desc or raw_repo in goal_title):
                    if any(w in q_title for w in ["repo", "repository", "setup", "initialize", "init", "scaffold", "build"]):
                        return q

    # 3. Calendar deadline matching
    elif act_type == "calendar_event":
        for q in quests:
            q_title = str(q.get("title", "")).lower()
            if any(w in act_title_lower for w in q_title.split() if len(w) > 3):
                return q

    return None

# Test scenarios
quests = [
    {
        "id": 65,
        "title": "Define Scope Action",
        "description": "Complete one small repeatable action toward Add two_sum project in github.",
        "category": "Learning",
        "quest_type": "habit",
        "skill": "Projects",
        "goal_title": "Add two_sum project in github",
        "goal_category": "Learning",
        "goal_type": "project",
        "assessment_required": False
    },
    {
        "id": 50,
        "title": "Conditional Branching & Logic",
        "description": "Predict execution paths through conditional expressions and truthiness rules.",
        "category": "Learning",
        "quest_type": "learning",
        "skill": "Python",
        "subject": "Python",
        "topic": "Branching & Logic",
        "goal_title": "I want to become a python developer",
        "goal_category": "Learning",
        "goal_type": "learning",
        "assessment_required": True
    },
    {
        "id": 60,
        "title": "Foundation Quest",
        "description": "Learn and explain the essential ideas behind I want to learn yoga.",
        "category": "Health",
        "quest_type": "learning",
        "skill": "Discipline",
        "goal_title": "I want to learn yoga",
        "goal_category": "Health",
        "goal_type": "learning",
        "assessment_required": False
    }
]

# Scenario 1: Two sum commit
act1 = DummyActivity("github_commit", "Two sum testing updates", "Two sum testing updates", {"repository": "life-rpg-python-test", "sha": "123"})
m1 = match_activity_to_quests(act1, quests)
print("Scenario 1 matched:", m1["id"] if m1 else None, m1["title"] if m1 else None)

# Scenario 2: Unrelated commit
act2 = DummyActivity("github_commit", "docs: update personal scratchpad notes", "notes", {"repository": "random-sandbox-scripts", "sha": "456"})
m2 = match_activity_to_quests(act2, quests)
print("Scenario 2 matched (should be None):", m2["id"] if m2 else None)

# Scenario 3: Test auth router commit from automated test
q_auth = [{
    "id": 101,
    "title": "Implement FastAPI Auth Router",
    "description": "Create JWT authentication router in repo life-rpg-api",
    "category": "Coding",
    "quest_type": "build",
    "skill": "Coding",
    "goal_title": "FastAPI Engine",
    "assessment_required": False
}]
act3 = DummyActivity("github_commit", "feat: implement auth router with JWT", "router commit", {"repository": "life-rpg-api", "sha": "789"})
m3 = match_activity_to_quests(act3, q_auth)
print("Scenario 3 matched (should be 101):", m3["id"] if m3 else None, m3["title"] if m3 else None)
