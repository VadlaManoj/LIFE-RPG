"""
Personalized Quest & Life-RPG Recommendation Engine (Phase 2).
Synthesizes real-world data (deadlines, calendar events, GitHub activity,
topic mastery/weak skills, and campaign state) to deliver high-priority,
actionable guidance from the Game Master.
"""

from __future__ import annotations
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class RecommendationItem(BaseModel):
    title: str
    urgency: str  # critical, high, normal, low
    category: str  # deadline, skill_reinforcement, project_velocity, habit
    reason: str
    suggested_quest_id: Optional[int] = None
    suggested_action: str
    icon: str = "sparkles"

class RecommendationResponse(BaseModel):
    headline: str
    summary: str
    top_recommendation: Optional[RecommendationItem] = None
    all_recommendations: List[RecommendationItem] = []
    generated_at: str

def generate_personalized_recommendations(
    active_quests: List[Dict[str, Any]],
    deadlines: List[Dict[str, Any]],
    weak_skills: List[str],
    github_active_repo: Optional[str] = None,
    recent_activity_count: int = 0
) -> RecommendationResponse:
    """
    Synthesizes multi-source context to produce deterministic, high-impact recommendations.
    """
    now = datetime.now()
    recommendations: List[RecommendationItem] = []

    # 1. Deadline Priority (highest precedence)
    urgent_deadlines = []
    for dl in deadlines:
        start_str = dl.get("start_time")
        if start_str:
            try:
                # Handle ISO format with or without Z
                clean_start = start_str.replace("Z", "")
                dl_dt = datetime.fromisoformat(clean_start)
                delta = dl_dt - now
                if timedelta(seconds=0) <= delta <= timedelta(days=2):
                    urgent_deadlines.append((dl, delta))
            except Exception:
                continue

    if urgent_deadlines:
        dl, delta = sorted(urgent_deadlines, key=lambda x: x[1])[0]
        hours_left = max(1, int(delta.total_seconds() // 3600))
        # Check if an active quest matches the deadline keywords
        summary = dl.get("summary", "")
        matching_q = None
        for q in active_quests:
            q_title = q.get("title", "").lower()
            if any(w in q_title for w in summary.lower().split() if len(w) > 3):
                matching_q = q
                break

        rec_title = f"Urgent: {summary}"
        reason = f"Calendar deadline is in ~{hours_left} hours ({summary})."
        suggested_action = f"Focus on '{matching_q.get('title')}' immediately." if matching_q else f"Complete your prep quest for {summary}."

        recommendations.append(RecommendationItem(
            title=rec_title,
            urgency="critical",
            category="deadline",
            reason=reason,
            suggested_quest_id=matching_q.get("id") if matching_q else None,
            suggested_action=suggested_action,
            icon="alert-triangle"
        ))

    # 2. Skill Reinforcement (Weak Skills)
    if weak_skills:
        weak_topic = weak_skills[0]
        # Look for a reinforcement or learning quest on this topic
        matching_q = next((q for q in active_quests if weak_topic.lower() in q.get("title", "").lower() or weak_topic.lower() in (q.get("topic") or "").lower()), None)
        recommendations.append(RecommendationItem(
            title=f"Reinforce: {weak_topic}",
            urgency="high",
            category="skill_reinforcement",
            reason=f"Diagnostic assessments flagged low confidence in {weak_topic}.",
            suggested_quest_id=matching_q.get("id") if matching_q else None,
            suggested_action=f"Work on '{matching_q.get('title')}' to rebuild confidence." if matching_q else f"Review {weak_topic} concepts before advancing to Boss battle.",
            icon="brain"
        ))

    # 3. GitHub Project Momentum
    if github_active_repo:
        project_q = next((q for q in active_quests if q.get("quest_type") in ["build", "project", "boss"]), None)
        if project_q:
            recommendations.append(RecommendationItem(
                title=f"Keep Committing to {github_active_repo}",
                urgency="normal",
                category="project_velocity",
                reason=f"Recent repository activity detected on {github_active_repo}.",
                suggested_quest_id=project_q.get("id"),
                suggested_action=f"Submit your recent commit as evidence for '{project_q.get('title')}'.",
                icon="git-commit"
            ))

    # 4. Standard Next Available Quest
    if not recommendations and active_quests:
        next_q = active_quests[0]
        recommendations.append(RecommendationItem(
            title=f"Next Objective: {next_q.get('title')}",
            urgency="normal",
            category="habit",
            reason="This is the next unlock in your primary campaign milestone.",
            suggested_quest_id=next_q.get("id"),
            suggested_action=f"Begin {next_q.get('title')} (estimated {next_q.get('estimated_minutes', 30)}m).",
            icon="swords"
        ))

    top_rec = recommendations[0] if recommendations else None
    headline = "Ready for Adventure"
    if top_rec:
        if top_rec.urgency == "critical":
            headline = "⚠️ Action Required: Approaching Deadline"
        elif top_rec.urgency == "high":
            headline = "🎯 Targeted Recommendation: Strengthen Mastery"
        else:
            headline = "✨ Your Next Recommended Move"

    summary = top_rec.reason if top_rec else "All goals and habits are up to date! Continue your quests."

    return RecommendationResponse(
        headline=headline,
        summary=summary,
        top_recommendation=top_rec,
        all_recommendations=recommendations,
        generated_at=now.isoformat()
    )
