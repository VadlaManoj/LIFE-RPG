import unittest
import json
from fastapi.testclient import TestClient
from app.main import app, SessionLocal, User, Goal, Campaign, Milestone, Quest, Quiz, TopicSkill, Skill, hash_password, token_for
from app.goal_engine import analyze_goal_deterministic, detect_learning_subject
from app.quiz_bank import QUIZ_BANK, BOSS_QUIZZES
from app.quiz_engine import mask_quiz_for_client
from app.evaluation_engine import evaluate_submission

class TestPhase1LearningEngine(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.session = SessionLocal()
        
        # Create test users
        self.user1_email = "tester1@liferpg.dev"
        self.user2_email = "tester2@liferpg.dev"
        
        # Clean up any leftover test data
        self.cleanup_user(self.user1_email)
        self.cleanup_user(self.user2_email)
        
        # User 1
        u1 = User(
            email=self.user1_email,
            password_hash=hash_password("password123"),
            name="DSA Hero",
            xp=100,
            level=1,
            coins=250,
            onboarding_done=True
        )
        self.session.add(u1)
        self.session.flush()
        self.u1_id = u1.id
        self.u1_token = token_for(u1.id)
        
        # User 2
        u2 = User(
            email=self.user2_email,
            password_hash=hash_password("password123"),
            name="Python Hero",
            xp=50,
            level=1,
            coins=100,
            onboarding_done=True
        )
        self.session.add(u2)
        self.session.flush()
        self.u2_id = u2.id
        self.u2_token = token_for(u2.id)
        
        self.session.commit()
        
    def tearDown(self):
        self.cleanup_user(self.user1_email)
        self.cleanup_user(self.user2_email)
        self.session.close()
        
    def cleanup_user(self, email):
        u = self.session.query(User).filter_by(email=email).first()
        if u:
            goals = self.session.query(Goal).filter_by(user_id=u.id).all()
            for g in goals:
                quests = self.session.query(Quest).filter_by(goal_id=g.id).all()
                for q in quests:
                    self.session.query(Quiz).filter_by(quest_id=q.id).delete()
                    self.session.delete(q)
                campaigns = self.session.query(Campaign).filter_by(goal_id=g.id).all()
                for c in campaigns:
                    self.session.query(Milestone).filter_by(campaign_id=c.id).delete()
                    self.session.delete(c)
                self.session.delete(g)
            self.session.query(TopicSkill).filter_by(user_id=u.id).delete()
            self.session.query(Skill).filter_by(user_id=u.id).delete()
            self.session.delete(u)
            self.session.commit()
            
    def auth_headers(self, token):
        return {"Authorization": f"Bearer {token}"}

    # 1. Goal AI & Deterministic Fallback Tests
    def test_dsa_goal_analysis(self):
        res = analyze_goal_deterministic("I want to learn DSA and crack tech interviews", deadline="8 weeks", minutes=45)
        self.assertEqual(res.subject, "DSA")
        self.assertEqual(res.goal_type, "learning")
        self.assertTrue(res.learning_required)
        self.assertTrue(res.assessment_required)
        self.assertIn("DSA", res.required_skills)
        
    def test_python_goal_analysis(self):
        res = analyze_goal_deterministic("Master Python from basics to OOP and APIs", deadline="6 weeks", minutes=30)
        self.assertEqual(res.subject, "Python")
        self.assertEqual(res.goal_type, "learning")
        self.assertTrue(res.learning_required)
        self.assertTrue(res.assessment_required)
        self.assertIn("Python", res.required_skills)
        
    def test_generic_task_goal_analysis(self):
        res = analyze_goal_deterministic("Run 5km every morning for fitness", minutes=30)
        self.assertIsNone(res.subject)
        self.assertEqual(res.goal_type, "habit")
        self.assertEqual(res.category, "Health")

    # 2. Dynamic Campaign & Learning Quest Generation
    def test_dsa_campaign_creation(self):
        resp = self.client.post("/api/goals", json={
            "title": "I want to learn DSA",
            "category": "Learning",
            "deadline": "8 weeks",
            "minutes": 45,
            "priority": "high",
            "level": "Intermediate"
        }, headers=self.auth_headers(self.u1_token))
        
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("campaign", data)
        self.assertIn("milestones", data)
        self.assertGreaterEqual(len(data["milestones"]), 5)
        
        # Check first learning quest
        quests = self.session.query(Quest).filter_by(goal_id=data["goal"]["id"]).all()
        self.assertTrue(len(quests) > 5)
        first_q = quests[0]
        self.assertEqual(first_q.subject, "DSA")
        self.assertTrue(first_q.assessment_required)
        self.assertEqual(first_q.status, "available")
        
        # Check that DSA topic skills were seeded
        topic_skills = self.session.query(TopicSkill).filter_by(user_id=self.u1_id, subject="DSA").all()
        self.assertTrue(len(topic_skills) >= 4)

    # 3. Quiz Generation & Anti-Answer-Leakage Security Test
    def test_quiz_generation_and_no_leakage(self):
        # Create DSA goal first
        g_resp = self.client.post("/api/goals", json={"title": "Master DSA"}, headers=self.auth_headers(self.u1_token))
        goal_id = g_resp.json()["goal"]["id"]
        quest = self.session.query(Quest).filter_by(goal_id=goal_id).first()
        
        # Fetch quiz
        q_resp = self.client.get(f"/api/quests/{quest.id}/quiz", headers=self.auth_headers(self.u1_token))
        self.assertEqual(q_resp.status_code, 200)
        quiz_data = q_resp.json()
        
        self.assertFalse(quiz_data["is_completed"])
        questions = quiz_data["questions"]
        self.assertGreaterEqual(len(questions), 2)
        
        # CRITICAL SECURITY CHECK: NO ANSWER LEAKAGE
        for q in questions:
            self.assertNotIn("correct_answer", q, "LEAK DETECTED: correct_answer exposed before submission!")
            self.assertNotIn("explanation", q, "LEAK DETECTED: explanation exposed before submission!")
            self.assertNotIn("keywords", q, "LEAK DETECTED: grading keywords exposed before submission!")
            self.assertNotIn("evaluation_criteria", q, "LEAK DETECTED: criteria exposed before submission!")

    # 4. Cross-User Security Test
    def test_cross_user_quiz_access_forbidden(self):
        # User 1 creates goal & quest
        g_resp = self.client.post("/api/goals", json={"title": "DSA for User 1"}, headers=self.auth_headers(self.u1_token))
        quest_id = self.session.query(Quest).filter_by(goal_id=g_resp.json()["goal"]["id"]).first().id
        
        # User 2 attempts to fetch User 1's quiz
        forbidden_resp = self.client.get(f"/api/quests/{quest_id}/quiz", headers=self.auth_headers(self.u2_token))
        self.assertEqual(forbidden_resp.status_code, 403)
        
        # User 2 attempts to submit to User 1's quiz
        forbidden_submit = self.client.post(f"/api/quests/{quest_id}/quiz/submit", json={"answers": {}}, headers=self.auth_headers(self.u2_token))
        self.assertEqual(forbidden_submit.status_code, 403)

    # 5. Quiz Submission, Multi-Type Evaluation & High Score Adaptive Branching
    def test_quiz_submission_high_score_advance(self):
        g_resp = self.client.post("/api/goals", json={"title": "Master DSA"}, headers=self.auth_headers(self.u1_token))
        goal_id = g_resp.json()["goal"]["id"]
        quest = self.session.query(Quest).filter_by(goal_id=goal_id).first()
        
        # Start quest & fetch quiz
        self.client.post(f"/api/quests/{quest.id}/start", headers=self.auth_headers(self.u1_token))
        quiz_resp = self.client.get(f"/api/quests/{quest.id}/quiz", headers=self.auth_headers(self.u1_token))
        
        # Retrieve internal quiz questions to prepare 100% correct answers
        quiz_obj = self.session.query(Quiz).filter_by(quest_id=quest.id).first()
        raw_questions = json.loads(quiz_obj.questions_data)
        
        perfect_answers = {}
        for q in raw_questions:
            perfect_answers[q["id"]] = q["correct_answer"]
            
        sub_resp = self.client.post(f"/api/quests/{quest.id}/quiz/submit", json={
            "answers": perfect_answers,
            "time_taken": 45
        }, headers=self.auth_headers(self.u1_token))
        
        self.assertEqual(sub_resp.status_code, 200)
        sub_data = sub_resp.json()
        
        self.assertGreaterEqual(sub_data["percentage"], 80)
        self.assertEqual(sub_data["adaptive"]["action"], "advance")
        self.assertEqual(sub_data["adaptive"]["tier"], "high")
        self.assertFalse(sub_data["adaptive"]["needs_reinforcement"])
        self.assertGreater(sub_data["earned_xp"], 0)
        self.assertGreater(sub_data["earned_coins"], 0)
        
        # Check that next quest was unlocked
        next_q = self.session.query(Quest).filter_by(goal_id=goal_id, order_index=1).first()
        if next_q:
            self.assertEqual(next_q.status, "available")

    # 6. Low Score -> Adaptive Reinforcement Quest Generation
    def test_quiz_submission_low_score_triggers_reinforcement(self):
        g_resp = self.client.post("/api/goals", json={"title": "Master DSA"}, headers=self.auth_headers(self.u1_token))
        goal_id = g_resp.json()["goal"]["id"]
        quest = self.session.query(Quest).filter_by(goal_id=goal_id).first()
        
        self.client.post(f"/api/quests/{quest.id}/start", headers=self.auth_headers(self.u1_token))
        self.client.get(f"/api/quests/{quest.id}/quiz", headers=self.auth_headers(self.u1_token))
        
        # Deliberately submit completely incorrect/empty answers
        bad_answers = {"bogus_id": "totally wrong answer"}
        sub_resp = self.client.post(f"/api/quests/{quest.id}/quiz/submit", json={
            "answers": bad_answers,
            "time_taken": 120
        }, headers=self.auth_headers(self.u1_token))
        
        self.assertEqual(sub_resp.status_code, 200)
        sub_data = sub_resp.json()
        
        self.assertLess(sub_data["percentage"], 60)
        self.assertTrue(sub_data["adaptive"]["needs_reinforcement"])
        self.assertIn(sub_data["adaptive"]["action"], ["reinforce", "revise"])
        
        # Verify targeted reinforcement quest was created
        reinforce_quest = self.session.query(Quest).filter_by(goal_id=goal_id, quest_type="reinforcement").first()
        self.assertIsNotNone(reinforce_quest)
        self.assertEqual(reinforce_quest.status, "available")
        self.assertEqual(reinforce_quest.parent_id, quest.id)
        self.assertEqual(reinforce_quest.subject, "DSA")

    # 7. Complete Python Flow & Boss Integration
    def test_python_curriculum_and_boss(self):
        g_resp = self.client.post("/api/goals", json={
            "title": "I want to learn Python",
            "category": "Learning",
            "deadline": "6 weeks",
            "minutes": 30
        }, headers=self.auth_headers(self.u2_token))
        
        self.assertEqual(g_resp.status_code, 200)
        goal_id = g_resp.json()["goal"]["id"]
        
        # Find Boss quest
        boss_quest = self.session.query(Quest).filter_by(goal_id=goal_id, is_boss=True).first()
        self.assertIsNotNone(boss_quest)
        self.assertEqual(boss_quest.subject, "Python")
        
        # Fetch Boss quiz
        boss_quiz_resp = self.client.get(f"/api/quests/{boss_quest.id}/quiz", headers=self.auth_headers(self.u2_token))
        self.assertEqual(boss_quiz_resp.status_code, 200)
        boss_questions = boss_quiz_resp.json()["questions"]
        self.assertGreaterEqual(len(boss_questions), 4)

    # 8. Game Master Context Integration
    def test_game_master_context(self):
        gm_resp = self.client.get("/api/game-master", headers=self.auth_headers(self.u1_token))
        self.assertEqual(gm_resp.status_code, 200)
        gm_data = gm_resp.json()
        self.assertIn("headline", gm_data)
        self.assertIn("message", gm_data)
        self.assertIn("tone", gm_data)

if __name__ == "__main__":
    unittest.main()
