"""
NLP Goal and Task Parsing Engine for LIFE RPG (Phase 2).
Converts natural language statements into structured goal/campaign/quest inputs.
Includes deterministic rule-based parsing with robust regex, datetime extraction,
and optional OpenAI structured inference fallback.
"""

from __future__ import annotations
import os
import re
import json
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel, Field

class NaturalLanguageParseResult(BaseModel):
    intent: str = Field("create_goal", description="Intent: create_goal, create_task, habit, learning, project")
    title: str = Field(..., description="Clean, punchy title for the quest/goal")
    raw_input: str = Field(..., description="Original input text")
    category: str = Field("productivity", description="Category: learning, project, habit, fitness, career, productivity")
    goal_type: str = Field("target", description="Goal type: habit, target, milestone")
    priority: str = Field("medium", description="Priority: low, medium, high, urgent")
    suggested_quest_type: str = Field("learning", description="learning, project, habit, challenge")
    deadline: Optional[str] = Field(None, description="ISO format datetime string if deadline detected")
    deadline_human: Optional[str] = Field(None, description="Human readable deadline string, e.g. 'Tomorrow 6:00 PM'")
    recurrence: Optional[str] = Field(None, description="none, daily, weekly, monthly")
    estimated_effort_minutes: int = Field(30, description="Estimated effort in minutes")
    related_skills: List[str] = Field(default_factory=list, description="Extracted skills or topics")
    suggested_xp: int = Field(50, description="Recommended base XP reward")
    suggested_coins: int = Field(25, description="Recommended base Coin reward")
    confidence: float = Field(0.9, description="Confidence score 0.0 - 1.0")
    explanation: str = Field("", description="Why this was parsed this way")

def _extract_deadline(text: str) -> tuple[Optional[str], Optional[str]]:
    """Deterministic extractor for common deadline expressions."""
    lower = text.lower()
    now = datetime.now()

    # Time detection (e.g., "6 pm", "18:00", "midnight")
    hour = 18
    minute = 0
    time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', lower)
    if time_match:
        val = int(time_match.group(1))
        meridiem = time_match.group(3)
        if meridiem == 'pm' and val < 12:
            hour = val + 12
        elif meridiem == 'am' and val == 12:
            hour = 0
        elif meridiem == 'am' or meridiem == 'pm':
            hour = val
        elif 0 <= val <= 23 and time_match.group(2):
            hour = val
        if time_match.group(2):
            minute = int(time_match.group(2))

    # Day detection
    target_dt = None
    human = None

    if "tonight" in lower:
        target_dt = now.replace(hour=22, minute=0, second=0, microsecond=0)
        human = "Tonight at 10:00 PM"
    elif "tomorrow" in lower:
        target_dt = (now + timedelta(days=1)).replace(hour=hour, minute=minute, second=0, microsecond=0)
        human = f"Tomorrow at {hour % 12 or 12}:{minute:02d} {'PM' if hour >= 12 else 'AM'}"
    else:
        days_of_week = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        for idx, day in enumerate(days_of_week):
            if day in lower:
                today_weekday = now.weekday()
                days_ahead = (idx - today_weekday) % 7
                if days_ahead == 0:
                    days_ahead = 7
                target_dt = (now + timedelta(days=days_ahead)).replace(hour=hour, minute=minute, second=0, microsecond=0)
                human = f"{day.capitalize()} at {hour % 12 or 12}:{minute:02d} {'PM' if hour >= 12 else 'AM'}"
                break

    if not target_dt and ("by " in lower or "before " in lower):
        # Default deadline within 24h
        target_dt = (now + timedelta(days=1)).replace(hour=hour, minute=minute, second=0, microsecond=0)
        human = f"Within 24 hours at {hour % 12 or 12}:{minute:02d} {'PM' if hour >= 12 else 'AM'}"

    if target_dt:
        return target_dt.isoformat(), human
    return None, None

def _extract_recurrence(text: str) -> Optional[str]:
    lower = text.lower()
    if any(k in lower for k in ["every day", "daily", "each day"]):
        return "daily"
    if any(k in lower for k in ["every week", "weekly", "once a week"]):
        return "weekly"
    if any(k in lower for k in ["monthly", "every month"]):
        return "monthly"
    return None

def _extract_skills(text: str) -> List[str]:
    skills = []
    lower = text.lower()
    skill_keywords = {
        "Python": ["python", "django", "fastapi", "flask"],
        "DSA": ["dsa", "data structures", "algorithms", "leetcode", "binary search", "recursion", "graph", "tree"],
        "JavaScript": ["javascript", "js", "typescript", "ts", "react", "vue", "node"],
        "SQL": ["sql", "database", "postgres", "sqlite", "mysql"],
        "System Design": ["system design", "architecture", "microservices"],
        "Fitness": ["workout", "walk", "running", "gym", "exercise", "run", "pushup", "cardio"],
        "Writing": ["report", "article", "documentation", "essay", "thesis", "assignment"]
    }
    for skill_name, patterns in skill_keywords.items():
        if any(p in lower for p in patterns):
            skills.append(skill_name)
    return skills

def parse_natural_language_goal(text: str) -> NaturalLanguageParseResult:
    """
    Parses natural language user input into structured goal/quest data.
    Uses robust deterministic extraction with fallback to OpenAI if API key available.
    """
    cleaned = (text or "").strip()
    if not cleaned:
        raise ValueError("Input text cannot be empty.")

    # 1. Try OpenAI if key is present
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            prompt = f"""
You are an expert RPG system planner. Parse the following user input into a structured Life-RPG goal/quest:
"{cleaned}"

Return a valid JSON object matching these exact keys:
{{
  "intent": "create_goal" | "create_task" | "habit" | "learning" | "project",
  "title": "Concise Quest/Goal Title",
  "category": "learning" | "project" | "habit" | "fitness" | "career" | "productivity",
  "goal_type": "habit" | "target" | "milestone",
  "priority": "low" | "medium" | "high" | "urgent",
  "suggested_quest_type": "learning" | "project" | "habit" | "challenge",
  "deadline": "ISO datetime string or null",
  "deadline_human": "e.g. Friday 6 PM or null",
  "recurrence": "daily" | "weekly" | "none" | null,
  "estimated_effort_minutes": 30,
  "related_skills": ["Skill1"],
  "suggested_xp": 50,
  "suggested_coins": 25,
  "confidence": 0.95,
  "explanation": "Brief rationale"
}}
Return ONLY valid JSON.
"""
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You output strictly valid JSON with no markdown wrapping."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            content = resp.choices[0].message.content.strip()
            if content.startswith("```"):
                content = re.sub(r"^```(?:json)?\n|\n```$", "", content)
            parsed_json = json.loads(content)
            parsed_json["raw_input"] = cleaned
            return NaturalLanguageParseResult(**parsed_json)
        except Exception:
            # Fall back to deterministic parser on any error
            pass

    # 2. Deterministic Parsing
    lower = cleaned.lower()
    deadline_iso, deadline_human = _extract_deadline(cleaned)
    recurrence = _extract_recurrence(cleaned)
    skills = _extract_skills(cleaned)

    # Category and suggested quest type
    category = "productivity"
    suggested_quest_type = "learning"
    goal_type = "target"
    priority = "medium"

    if recurrence == "daily":
        goal_type = "habit"
        suggested_quest_type = "habit"
        category = "habit"
    elif any(k in lower for k in ["walk", "run", "workout", "exercise", "gym", "steps", "fitness"]):
        category = "fitness"
        suggested_quest_type = "habit" if recurrence else "challenge"
    elif any(k in lower for k in ["build", "project", "create", "deploy", "repo", "api", "app"]):
        category = "project"
        suggested_quest_type = "project"
    elif any(k in lower for k in ["study", "learn", "practice", "dsa", "python", "interview", "prep", "exam", "quiz"]):
        category = "learning"
        suggested_quest_type = "learning"
    elif any(k in lower for k in ["report", "document", "submit", "assignment", "slides"]):
        category = "productivity"
        suggested_quest_type = "project"

    if deadline_iso or "urgent" in lower or "asap" in lower:
        priority = "high"
    if "interview" in lower or "exam" in lower or "tomorrow" in lower:
        priority = "urgent" if "tomorrow" in lower or "tonight" in lower else "high"

    # Title cleanup
    title = cleaned
    remove_prefixes = [
        r"^i need to\s+",
        r"^i want to\s+",
        r"^tomorrow i need to\s+",
        r"^please help me\s+",
        r"^remind me to\s+",
        r"^i have to\s+",
    ]
    for pref in remove_prefixes:
        title = re.sub(pref, "", title, flags=re.IGNORECASE)
    title = title.strip().capitalize()
    if len(title) > 60:
        title = title[:57] + "..."

    # Estimate minutes
    effort = 45
    min_match = re.search(r'(\d+)\s*(?:hour|hr|h)', lower)
    if min_match:
        effort = int(min_match.group(1)) * 60
    else:
        min_match2 = re.search(r'(\d+)\s*(?:minute|min|m)', lower)
        if min_match2:
            effort = int(min_match2.group(1))

    # Reward calculation
    base_xp = 50 + (effort // 10) * 5
    if priority in ["high", "urgent"]:
        base_xp = int(base_xp * 1.3)
    base_coins = max(10, base_xp // 2)

    return NaturalLanguageParseResult(
        intent="habit" if recurrence else ("create_campaign" if "prepare" in lower or "interview" in lower else "create_task"),
        title=title,
        raw_input=cleaned,
        category=category,
        goal_type=goal_type,
        priority=priority,
        suggested_quest_type=suggested_quest_type,
        deadline=deadline_iso,
        deadline_human=deadline_human,
        recurrence=recurrence,
        estimated_effort_minutes=effort,
        related_skills=skills if skills else ["General"],
        suggested_xp=base_xp,
        suggested_coins=base_coins,
        confidence=0.88,
        explanation=f"Identified as {category} task with {priority} priority and {effort} min estimated duration."
    )
