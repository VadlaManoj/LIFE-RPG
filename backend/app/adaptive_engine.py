from datetime import datetime
import json
from typing import Dict, Any, Optional, Tuple

def update_topic_skill(
    session,
    user_id: int,
    subject: str,
    topic: str,
    score_pct: float,
    weak_subtopics: list = None,
    TopicSkillModel = None
) -> Dict[str, Any]:
    """Updates or creates a TopicSkill entry using historical exponential moving average."""
    if not TopicSkillModel:
        return {}
        
    ts = session.query(TopicSkillModel).filter_by(
        user_id=user_id,
        subject=subject,
        topic=topic
    ).first()
    
    if not ts:
        initial_confidence = round(max(0.2, min(1.0, score_pct / 100.0)), 2)
        initial_mastery = round(max(5.0, min(100.0, score_pct)), 1)
        ts = TopicSkillModel(
            user_id=user_id,
            subject=subject,
            topic=topic,
            mastery=initial_mastery,
            confidence=initial_confidence,
            attempts=1,
            last_score=score_pct,
            last_assessed=datetime.utcnow(),
            weak_subtopics=json.dumps(weak_subtopics or [])
        )
        session.add(ts)
    else:
        # Exponential moving average: 40% current attempt, 60% historical
        alpha = 0.4
        ts.attempts += 1
        ts.last_score = score_pct
        ts.last_assessed = datetime.utcnow()
        
        # Calculate new confidence and mastery gradually
        target_conf = max(0.1, min(1.0, score_pct / 100.0))
        ts.confidence = round((1 - alpha) * ts.confidence + alpha * target_conf, 2)
        ts.mastery = round(min(100.0, max(0.0, (1 - alpha) * ts.mastery + alpha * score_pct)), 1)
        
        if weak_subtopics:
            existing = json.loads(ts.weak_subtopics) if ts.weak_subtopics else []
            combined = list(dict.fromkeys(existing + weak_subtopics))
            ts.weak_subtopics = json.dumps(combined)
            
    session.flush()
    return {
        "topic": topic,
        "mastery": ts.mastery,
        "confidence": ts.confidence,
        "attempts": ts.attempts,
        "last_score": ts.last_score
    }

def decide_adaptive_progression(
    score_pct: float,
    subject: str,
    topic: str,
    subtopic: str,
    current_difficulty: int,
    consecutive_reinforcements: int = 0,
    weak_areas: list = None
) -> Dict[str, Any]:
    """
    Evaluates assessment performance to determine the next adaptive action:
    - High (>= 80%): increase difficulty / unlock next topic
    - Medium (60 - 79%): continue normal campaign progression
    - Low (40 - 59%): generate targeted reinforcement quest on weak area
    - Very Low (< 40%): generate concept-revision quest with easier assessment
    Loop prevention: If already reinforced >= 2 times, advance with guidance.
    """
    weak_label = weak_areas[0] if weak_areas else (subtopic or topic)
    
    if score_pct >= 80:
        return {
            "action": "advance",
            "tier": "high",
            "next_difficulty": min(5, current_difficulty + 1),
            "message": f"Mastery demonstrated! Increasing difficulty and unlocking next challenge in {topic}.",
            "needs_reinforcement": False
        }
    elif score_pct >= 60:
        return {
            "action": "standard",
            "tier": "medium",
            "next_difficulty": current_difficulty,
            "message": f"Solid performance on {topic}. Advancing along the campaign path.",
            "needs_reinforcement": False
        }
    else:
        # Loop prevention: prevent infinite reinforcement loops
        if consecutive_reinforcements >= 2:
            return {
                "action": "standard",
                "tier": "assisted_advance",
                "next_difficulty": max(1, current_difficulty - 1),
                "message": f"Repeated practice completed for {topic}. Moving forward with foundational guidance to prevent stall.",
                "needs_reinforcement": False
            }
            
        if score_pct >= 40:
            return {
                "action": "reinforce",
                "tier": "low",
                "next_difficulty": max(1, current_difficulty - 1),
                "weak_concept": weak_label,
                "message": f"Weak spot detected in {weak_label}. Generating targeted reinforcement quest.",
                "needs_reinforcement": True,
                "quest_title": f"Reinforcement: {topic} ({weak_label})",
                "quest_desc": f"Strengthen understanding of {weak_label} with a focused, targeted drill."
            }
        else:
            return {
                "action": "revise",
                "tier": "very_low",
                "next_difficulty": 1,
                "weak_concept": weak_label,
                "message": f"Core concepts in {topic} need revision. Generating foundational concept-revision quest.",
                "needs_reinforcement": True,
                "quest_title": f"Concept Revision: {topic} Fundamentals",
                "quest_desc": f"Review essential concepts and patterns for {topic} before proceeding."
            }
