import json, copy, os, re
from typing import List, Dict, Any, Optional
from app.quiz_bank import QUIZ_BANK, BOSS_QUIZZES

def mask_question_for_client(q: Dict[str, Any]) -> Dict[str, Any]:
    """Strip all answers, explanations, keywords, and grading rubrics before sending to client."""
    client_q = copy.deepcopy(q)
    client_q.pop("correct_answer", None)
    client_q.pop("explanation", None)
    client_q.pop("keywords", None)
    client_q.pop("evaluation_criteria", None)
    return client_q

def mask_quiz_for_client(questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [mask_question_for_client(q) for q in questions]

def get_questions_for_topic(subject: str, topic: str, count: int = 3, difficulty: int = 2) -> List[Dict[str, Any]]:
    subject_bank = QUIZ_BANK.get(subject, {})
    
    # Check exact topic
    pool = list(subject_bank.get(topic, []))
    
    # If not enough in topic, gather from related topics in subject
    if len(pool) < count:
        for other_topic, questions in subject_bank.items():
            if other_topic != topic:
                pool.extend(questions)
    
    # Pick questions (sorted by closeness to difficulty or take up to count)
    pool.sort(key=lambda q: abs(q.get("difficulty", 2) - difficulty))
    selected = pool[:count]
    
    # Return deep copies so modifications don't mutate the static bank
    return [copy.deepcopy(q) for q in selected]

def get_boss_quiz(subject: str) -> List[Dict[str, Any]]:
    boss_pool = BOSS_QUIZZES.get(subject)
    if boss_pool:
        return [copy.deepcopy(q) for q in boss_pool]
    # Fallback to general bank
    return get_questions_for_topic(subject, "Foundations" if subject == "DSA" else "Basics", count=4, difficulty=5)

def get_reinforcement_quiz(subject: str, topic: str, weak_subtopic: str = "", difficulty: int = 1) -> List[Dict[str, Any]]:
    """Generate a targeted, shorter reinforcement quiz focused on the weak concept."""
    base_questions = get_questions_for_topic(subject, topic, count=3, difficulty=max(1, difficulty - 1))
    
    # If a specific subtopic was marked weak, prioritize matching questions
    if weak_subtopic:
        filtered = [q for q in base_questions if q.get("subtopic", "").lower() == weak_subtopic.lower()]
        if filtered:
            return filtered[:2]
            
    # Return 2 focused questions for reinforcement
    return base_questions[:2]

async def generate_quiz_for_quest(
    quest_title: str,
    subject: str,
    topic: str,
    subtopic: str,
    difficulty: int,
    learning_objective: str,
    is_boss: bool = False,
    is_reinforcement: bool = False,
    ai_json_func = None
) -> List[Dict[str, Any]]:
    """Generate or retrieve assessment questions for a quest. Uses AI if available with fallback to deterministic bank."""
    if is_boss:
        return get_boss_quiz(subject)
        
    if is_reinforcement:
        return get_reinforcement_quiz(subject, topic, weak_subtopic=subtopic, difficulty=difficulty)

    # Attempt AI quiz generation if OpenAI is configured
    if ai_json_func and os.getenv("OPENAI_API_KEY"):
        prompt = f"""
Generate an assessment quiz for a coding learning quest.
Subject: {subject}
Topic: {topic}
Subtopic: {subtopic}
Difficulty (1-5): {difficulty}
Learning Objective: {learning_objective}

Return a JSON array of 3 questions with different types (such as mcq, output_prediction, debugging, short_answer, coding_problem).
Each question JSON object must contain:
- id: unique string
- question_type: one of 'mcq', 'output_prediction', 'debugging', 'short_answer', 'coding_problem'
- question: clear question text or code snippet
- options: array of 4 choices (empty array if not mcq)
- correct_answer: index (0-3) for mcq, or string answer for others
- explanation: educational explanation
- points: 10, 15, or 20
- topic: {topic}
- subtopic: {subtopic}
- difficulty: {difficulty}
"""
        fallback_questions = get_questions_for_topic(subject, topic, count=3, difficulty=difficulty)
        try:
            ai_result = await ai_json_func(prompt, fallback_questions)
            if isinstance(ai_result, list) and len(ai_result) >= 2 and all("question" in q and "correct_answer" in q for q in ai_result):
                return ai_result
        except Exception:
            pass

    # Deterministic fallback
    return get_questions_for_topic(subject, topic, count=3, difficulty=difficulty)
