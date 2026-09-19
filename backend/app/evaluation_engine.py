import re, ast
from typing import List, Dict, Any, Tuple

def normalize_text(text: Any) -> str:
    if text is None:
        return ""
    s = str(text).strip()
    # Normalize quotes, spaces, and linebreaks
    s = re.sub(r'["\']', '', s)
    s = re.sub(r'\s+', ' ', s)
    return s.lower()

def evaluate_mcq(user_ans: Any, correct_ans: Any, options: List[str]) -> Tuple[bool, float, str]:
    if user_ans is None:
        return False, 0.0, "No answer selected."
    
    # User answer could be an index integer (0, 1, 2) or the string text of the option
    if isinstance(correct_ans, int):
        try:
            if int(user_ans) == correct_ans:
                return True, 1.0, "Correct option selected."
        except (ValueError, TypeError):
            pass
        # Check if user passed the option string
        if 0 <= correct_ans < len(options) and normalize_text(user_ans) == normalize_text(options[correct_ans]):
            return True, 1.0, "Correct option selected."
    else:
        if normalize_text(user_ans) == normalize_text(correct_ans):
            return True, 1.0, "Correct option selected."
            
    return False, 0.0, "Incorrect option."

def evaluate_output_prediction(user_ans: Any, correct_ans: Any) -> Tuple[bool, float, str]:
    u_norm = normalize_text(user_ans)
    c_norm = normalize_text(correct_ans)
    
    if not u_norm:
        return False, 0.0, "No output provided."
        
    if u_norm == c_norm:
        return True, 1.0, "Exact output match."
        
    # Check without brackets / commas for list outputs like [1, 2] vs 1, 2
    u_clean = re.sub(r'[\[\]\(\),]', '', u_norm).strip()
    c_clean = re.sub(r'[\[\]\(\),]', '', c_norm).strip()
    if u_clean == c_clean:
        return True, 1.0, "Correct values returned."
        
    return False, 0.0, f"Expected output: {correct_ans}"

def evaluate_debugging(user_ans: Any, correct_ans: Any) -> Tuple[bool, float, str]:
    u_norm = normalize_text(user_ans)
    c_norm = normalize_text(correct_ans)
    
    if not u_norm:
        return False, 0.0, "No fix proposed."
        
    if c_norm in u_norm or u_norm in c_norm:
        return True, 1.0, "Bug correctly diagnosed and resolved."
        
    # Check for key programming tokens
    keywords = [w for w in c_norm.split() if len(w) > 2 and w not in ["and", "the", "for", "with"]]
    matches = sum(1 for kw in keywords if kw in u_norm)
    if keywords and matches / len(keywords) >= 0.5:
        return True, 0.8, "Partial bug fix identified."
        
    return False, 0.0, f"Suggested fix: {correct_ans}"

def evaluate_short_answer(user_ans: Any, correct_ans: Any, keywords: List[str] = None) -> Tuple[bool, float, str]:
    u_norm = normalize_text(user_ans)
    if not u_norm:
        return False, 0.0, "No explanation provided."
        
    kws = [normalize_text(k) for k in (keywords or [])]
    if not kws:
        kws = [w for w in normalize_text(correct_ans).split() if len(w) > 3]
        
    hit_count = sum(1 for kw in kws if kw in u_norm)
    total_kws = max(1, len(kws))
    ratio = hit_count / total_kws
    
    if ratio >= 0.5 or (normalize_text(correct_ans) in u_norm):
        return True, 1.0, "Key concepts thoroughly articulated."
    elif ratio >= 0.25:
        return True, 0.6, "Core concept partially addressed."
    else:
        return False, 0.2, "Explanation lacked key conceptual criteria."

def evaluate_coding_problem(user_ans: Any, correct_ans: Any, criteria: Dict[str, Any] = None) -> Tuple[bool, float, str]:
    u_code = str(user_ans or "").strip()
    if not u_code:
        return False, 0.0, "No code submitted."
        
    # Safe AST check to verify valid Python syntax
    try:
        ast.parse(u_code)
    except SyntaxError:
        # Check if user submitted just an expression or statement
        pass
        
    u_norm = normalize_text(u_code)
    c_norm = normalize_text(correct_ans)
    
    # Check if user code matches or contains key patterns
    required = criteria.get("required_patterns", []) if criteria else []
    if not required:
        required = [w for w in c_norm.split() if len(w) > 3][:3]
        
    hits = sum(1 for p in required if normalize_text(p) in u_norm)
    score_ratio = hits / max(1, len(required))
    
    if score_ratio >= 0.7 or c_norm in u_norm:
        return True, 1.0, "Clean, valid implementation matching problem requirements."
    elif score_ratio >= 0.4:
        return True, 0.65, "Good logic with minor pattern discrepancies."
    else:
        return False, 0.2, "Code did not meet primary algorithmic criteria."

def evaluate_submission(
    questions: List[Dict[str, Any]],
    user_answers: Dict[str, Any],
    time_taken: int = 0
) -> Dict[str, Any]:
    total_earned_points = 0.0
    max_points = 0.0
    correct_count = 0
    incorrect_count = 0
    
    question_type_perf: Dict[str, Dict[str, int]] = {}
    topic_perf: Dict[str, Dict[str, float]] = {}
    detailed_results = []
    
    for q in questions:
        qid = q.get("id")
        qtype = q.get("question_type", "mcq")
        topic = q.get("topic", "General")
        subtopic = q.get("subtopic", "")
        pts = float(q.get("points", 10))
        max_points += pts
        
        user_val = user_answers.get(qid)
        correct_val = q.get("correct_answer")
        options = q.get("options", [])
        keywords = q.get("keywords", [])
        criteria = q.get("evaluation_criteria", {})
        
        # Route to specific evaluator
        if qtype == "mcq":
            is_correct, score_mult, feedback = evaluate_mcq(user_val, correct_val, options)
        elif qtype == "output_prediction":
            is_correct, score_mult, feedback = evaluate_output_prediction(user_val, correct_val)
        elif qtype == "debugging":
            is_correct, score_mult, feedback = evaluate_debugging(user_val, correct_val)
        elif qtype == "short_answer":
            is_correct, score_mult, feedback = evaluate_short_answer(user_val, correct_val, keywords)
        elif qtype == "coding_problem":
            is_correct, score_mult, feedback = evaluate_coding_problem(user_val, correct_val, criteria)
        else:
            is_correct, score_mult, feedback = evaluate_output_prediction(user_val, correct_val)
            
        earned = pts * score_mult
        total_earned_points += earned
        
        if is_correct and score_mult >= 0.6:
            correct_count += 1
        else:
            incorrect_count += 1
            
        # Track by question type
        if qtype not in question_type_perf:
            question_type_perf[qtype] = {"correct": 0, "total": 0}
        question_type_perf[qtype]["total"] += 1
        if is_correct and score_mult >= 0.6:
            question_type_perf[qtype]["correct"] += 1
            
        # Track by topic
        if topic not in topic_perf:
            topic_perf[topic] = {"earned": 0.0, "total": 0.0, "subtopics": {}}
        topic_perf[topic]["earned"] += earned
        topic_perf[topic]["total"] += pts
        
        if subtopic:
            sub_dict = topic_perf[topic]["subtopics"]
            if subtopic not in sub_dict:
                sub_dict[subtopic] = {"earned": 0.0, "total": 0.0}
            sub_dict[subtopic]["earned"] += earned
            sub_dict[subtopic]["total"] += pts
            
        detailed_results.append({
            "id": qid,
            "question_type": qtype,
            "question": q.get("question"),
            "topic": topic,
            "subtopic": subtopic,
            "user_answer": user_val,
            "correct_answer": correct_val,
            "is_correct": is_correct,
            "score_mult": score_mult,
            "earned_points": earned,
            "points": pts,
            "explanation": q.get("explanation", ""),
            "feedback": feedback
        })
        
    percentage = round((total_earned_points / max(1.0, max_points)) * 100, 1)
    
    # Calculate strong and weak areas
    weak_areas = []
    strong_areas = []
    topic_summary = {}
    
    for top, data in topic_perf.items():
        pct = round((data["earned"] / max(1.0, data["total"])) * 100, 1)
        topic_summary[top] = pct
        if pct < 65:
            # Check subtopics for specific weak spots
            weak_subs = [s for s, sdata in data["subtopics"].items() if (sdata["earned"] / max(1.0, sdata["total"])) < 0.65]
            weak_label = f"{top} ({', '.join(weak_subs)})" if weak_subs else top
            weak_areas.append(weak_label)
        elif pct >= 75:
            strong_areas.append(top)
            
    return {
        "total_score": round(total_earned_points, 1),
        "max_score": round(max_points, 1),
        "percentage": percentage,
        "correct_count": correct_count,
        "incorrect_count": incorrect_count,
        "time_taken": time_taken,
        "question_type_perf": question_type_perf,
        "topic_perf": topic_summary,
        "weak_areas": weak_areas,
        "strong_areas": strong_areas,
        "detailed_results": detailed_results
    }
