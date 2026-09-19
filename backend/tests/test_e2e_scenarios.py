import unittest
import json
from fastapi.testclient import TestClient
from app.main import app, SessionLocal, User, Goal, Campaign, Milestone, Quest, Quiz, TopicSkill, Skill, hash_password, token_for

class TestEndToEndScenarios(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.session = SessionLocal()
        
        self.email = "e2e_hero@liferpg.dev"
        self.cleanup()
        
        user = User(
            email=self.email,
            password_hash=hash_password("password123"),
            name="E2E Champion",
            xp=0,
            level=1,
            coins=250,
            onboarding_done=True
        )
        self.session.add(user)
        self.session.commit()
        self.user_id = user.id
        self.token = token_for(user.id)
        
    def tearDown(self):
        self.cleanup()
        self.session.close()
        
    def cleanup(self):
        u = self.session.query(User).filter_by(email=self.email).first()
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

    def auth(self):
        return {"Authorization": f"Bearer {self.token}"}

    def test_dsa_complete_lifecycle(self):
        # 1. USER Creates "I want to learn DSA"
        # 2. AI analyzes goal
        analyze_resp = self.client.post("/api/goals/analyze", json={
            "title": "I want to learn DSA",
            "category": "Learning",
            "minutes": 45,
            "priority": "high"
        }, headers=self.auth())
        self.assertEqual(analyze_resp.status_code, 200)
        analysis = analyze_resp.json()
        self.assertEqual(analysis["subject"], "DSA")
        self.assertTrue(analysis["learning_required"])
        self.assertTrue(analysis["assessment_required"])
        
        # 3. Campaign & Milestones generated
        create_resp = self.client.post("/api/goals", json={
            "title": "I want to learn DSA",
            "category": "Learning",
            "minutes": 45,
            "priority": "high",
            "level": "Intermediate"
        }, headers=self.auth())
        self.assertEqual(create_resp.status_code, 200)
        c_data = create_resp.json()
        goal_id = c_data["goal"]["id"]
        
        # 4. Learning Quests generated (identifies DSA topics)
        quests = self.session.query(Quest).filter_by(goal_id=goal_id).order_by(Quest.order_index).all()
        self.assertGreaterEqual(len(quests), 5)
        first_q = quests[0]
        self.assertEqual(first_q.subject, "DSA")
        self.assertTrue(first_q.assessment_required)
        
        # 5. User opens Learning Quest & Assessment generated
        quiz_resp = self.client.get(f"/api/quests/{first_q.id}/quiz", headers=self.auth())
        self.assertEqual(quiz_resp.status_code, 200)
        quiz_data = quiz_resp.json()
        self.assertFalse(quiz_data["is_completed"])
        questions = quiz_data["questions"]
        self.assertGreaterEqual(len(questions), 2)
        # Verify no answer leakage
        for q in questions:
            self.assertNotIn("correct_answer", q)
            self.assertNotIn("explanation", q)
            
        # 6. User answers quiz (Weak performance branch)
        bad_answers = {q["id"]: "completely wrong answer" for q in questions}
        submit_resp1 = self.client.post(f"/api/quests/{first_q.id}/quiz/submit", json={
            "answers": bad_answers,
            "time_taken": 60
        }, headers=self.auth())
        self.assertEqual(submit_resp1.status_code, 200)
        res1 = submit_resp1.json()
        
        # 7. Score calculated, weak areas detected, XP awarded, reinforcement generated
        self.assertLess(res1["percentage"], 60)
        self.assertGreater(len(res1["weak_areas"]), 0)
        self.assertTrue(res1["adaptive"]["needs_reinforcement"])
        self.assertGreater(res1["earned_xp"], 0)
        self.assertGreater(res1["earned_coins"], 0)
        
        # Verify reinforcement quest exists
        reinf_q = self.session.query(Quest).filter_by(goal_id=goal_id, quest_type="reinforcement").first()
        self.assertIsNotNone(reinf_q)
        self.assertEqual(reinf_q.status, "available")
        
        # 8. User completes reinforcement quest with HIGH score
        reinf_quiz_resp = self.client.get(f"/api/quests/{reinf_q.id}/quiz", headers=self.auth())
        reinf_quiz_data = reinf_quiz_resp.json()
        reinf_questions = reinf_quiz_data["questions"]
        
        # Read raw answers to answer correctly
        raw_quiz = self.session.query(Quiz).filter_by(quest_id=reinf_q.id).first()
        raw_q_list = json.loads(raw_quiz.questions_data)
        correct_answers = {q["id"]: q["correct_answer"] for q in raw_q_list}
        
        submit_resp2 = self.client.post(f"/api/quests/{reinf_q.id}/quiz/submit", json={
            "answers": correct_answers,
            "time_taken": 30
        }, headers=self.auth())
        self.assertEqual(submit_resp2.status_code, 200)
        res2 = submit_resp2.json()
        self.assertGreaterEqual(res2["percentage"], 80)
        self.assertFalse(res2["adaptive"]["needs_reinforcement"])
        
        # 9. Next quest in main campaign is unlocked
        self.session.expire_all()
        next_q = self.session.query(Quest).filter_by(goal_id=goal_id, order_index=1).first()
        self.assertEqual(next_q.status, "available")
        
        # 10. DSA Boss Battle
        boss_q = self.session.query(Quest).filter_by(goal_id=goal_id, is_boss=True).first()
        self.assertIsNotNone(boss_q)
        boss_quiz_resp = self.client.get(f"/api/quests/{boss_q.id}/quiz", headers=self.auth())
        self.assertEqual(boss_quiz_resp.status_code, 200)
        boss_raw = self.session.query(Quiz).filter_by(quest_id=boss_q.id).first()
        boss_questions = json.loads(boss_raw.questions_data)
        
        boss_answers = {q["id"]: q["correct_answer"] for q in boss_questions}
        boss_submit = self.client.post(f"/api/quests/{boss_q.id}/quiz/submit", json={
            "answers": boss_answers,
            "time_taken": 180
        }, headers=self.auth())
        self.assertEqual(boss_submit.status_code, 200)
        boss_res = boss_submit.json()
        self.assertGreaterEqual(boss_res["percentage"], 80)
        
        # 11. Verify Skill & TopicSkill updates
        ts_rows = self.session.query(TopicSkill).filter_by(user_id=self.user_id, subject="DSA").all()
        self.assertGreater(len(ts_rows), 0)
        dsa_skill = self.session.query(Skill).filter_by(user_id=self.user_id, name="DSA").first()
        self.assertIsNotNone(dsa_skill)
        self.assertGreater(dsa_skill.xp, 0)
        self.assertGreater(dsa_skill.progress, 0)

    def test_python_complete_lifecycle(self):
        # 1. USER Creates "I want to learn Python"
        create_resp = self.client.post("/api/goals", json={
            "title": "I want to learn Python",
            "category": "Learning",
            "minutes": 30,
            "priority": "medium",
            "level": "Beginner"
        }, headers=self.auth())
        self.assertEqual(create_resp.status_code, 200)
        data = create_resp.json()
        goal_id = data["goal"]["id"]
        
        # 2. Learning Quests
        quests = self.session.query(Quest).filter_by(goal_id=goal_id).order_by(Quest.order_index).all()
        self.assertGreaterEqual(len(quests), 5)
        first_q = quests[0]
        self.assertEqual(first_q.subject, "Python")
        
        # 3. Start & Take assessment
        quiz_resp = self.client.get(f"/api/quests/{first_q.id}/quiz", headers=self.auth())
        self.assertEqual(quiz_resp.status_code, 200)
        raw_quiz = self.session.query(Quiz).filter_by(quest_id=first_q.id).first()
        raw_questions = json.loads(raw_quiz.questions_data)
        
        perfect_answers = {q["id"]: q["correct_answer"] for q in raw_questions}
        sub_resp = self.client.post(f"/api/quests/{first_q.id}/quiz/submit", json={
            "answers": perfect_answers,
            "time_taken": 40
        }, headers=self.auth())
        self.assertEqual(sub_resp.status_code, 200)
        sub_res = sub_resp.json()
        self.assertGreaterEqual(sub_res["percentage"], 80)
        self.assertEqual(sub_res["adaptive"]["action"], "advance")
        
        # 4. Boss Challenge
        boss_q = self.session.query(Quest).filter_by(goal_id=goal_id, is_boss=True).first()
        self.assertIsNotNone(boss_q)
        boss_quiz_resp = self.client.get(f"/api/quests/{boss_q.id}/quiz", headers=self.auth())
        self.assertEqual(boss_quiz_resp.status_code, 200)
        
        # 5. Topic skills endpoint
        topics_resp = self.client.get("/api/skills/Python/topics", headers=self.auth())
        self.assertEqual(topics_resp.status_code, 200)
        topic_list = topics_resp.json()
        self.assertGreaterEqual(len(topic_list), 4)

    def test_non_learning_goal_continues_working(self):
        # Verify non-learning goals (habit / personal) continue working without breaking
        create_resp = self.client.post("/api/goals", json={
            "title": "Drink 3 liters of water every day",
            "category": "Health",
            "minutes": 15,
            "priority": "medium"
        }, headers=self.auth())
        self.assertEqual(create_resp.status_code, 200)
        data = create_resp.json()
        self.assertEqual(data["goal"]["category"], "Health")
        
        quests = self.session.query(Quest).filter_by(goal_id=data["goal"]["id"]).all()
        self.assertGreaterEqual(len(quests), 3)
        # Complete via standard complete endpoint
        comp_resp = self.client.post(f"/api/quests/{quests[0].id}/complete", json={
            "score": 1.0
        }, headers=self.auth())
        self.assertEqual(comp_resp.status_code, 200)
        self.assertGreater(comp_resp.json()["earned_xp"], 0)

if __name__ == "__main__":
    unittest.main()
