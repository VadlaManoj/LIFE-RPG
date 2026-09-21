"""
Automated tests for LIFE RPG Authentication flow:
- successful registration (both /signup and /register)
- duplicate registration rejection
- invalid registration data (short password, missing fields)
- successful login
- wrong password rejection
- nonexistent user rejection
- authenticated session verification (/api/me)
- protected endpoint access with and without token
- logout functionality (/api/auth/logout)
"""

import unittest
from fastapi.testclient import TestClient
from app.main import app, SessionLocal, User, hash_password


class TestAuthentication(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.db = SessionLocal()

        # Clean up any leftover test accounts
        test_emails = [
            'authtest_new@example.com',
            'authtest_existing@example.com',
            'authtest_register_alias@example.com'
        ]
        cls.db.query(User).filter(User.email.in_(test_emails)).delete(synchronize_session=False)
        cls.db.commit()

        # Seed an existing user
        cls.existing_user = User(
            email='authtest_existing@example.com',
            password_hash=hash_password('ValidPass123!'),
            name='ExistingHero'
        )
        cls.db.add(cls.existing_user)
        cls.db.commit()
        cls.db.refresh(cls.existing_user)

    @classmethod
    def tearDownClass(cls):
        test_emails = [
            'authtest_new@example.com',
            'authtest_existing@example.com',
            'authtest_register_alias@example.com'
        ]
        cls.db.query(User).filter(User.email.in_(test_emails)).delete(synchronize_session=False)
        cls.db.commit()
        cls.db.close()

    def test_01_successful_registration_signup(self):
        """Test registering a new user via /api/auth/signup."""
        resp = self.client.post('/api/auth/signup', json={
            'email': 'authtest_new@example.com',
            'password': 'StrongPassword123',
            'name': 'NewHero'
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('token', data)
        self.assertIn('user', data)
        self.assertEqual(data['user']['email'], 'authtest_new@example.com')
        self.assertEqual(data['user']['name'], 'NewHero')
        self.assertNotIn('password_hash', data['user'])

    def test_02_successful_registration_register_alias(self):
        """Test registering a new user via /api/auth/register alias."""
        resp = self.client.post('/api/auth/register', json={
            'email': 'authtest_register_alias@example.com',
            'password': 'StrongPassword123',
            'name': 'AliasHero'
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('token', data)
        self.assertEqual(data['user']['email'], 'authtest_register_alias@example.com')

    def test_03_duplicate_registration(self):
        """Test duplicate registration returns 400 with descriptive error."""
        resp = self.client.post('/api/auth/signup', json={
            'email': 'authtest_existing@example.com',
            'password': 'AnotherPassword123',
            'name': 'DuplicateHero'
        })
        self.assertEqual(resp.status_code, 400)
        data = resp.json()
        self.assertIn('already exists', data['detail'])

    def test_04_invalid_registration_data(self):
        """Test invalid registration payload (short password) returns 422."""
        resp = self.client.post('/api/auth/signup', json={
            'email': 'authtest_shortpass@example.com',
            'password': '123',  # min_length is 6
            'name': 'ShortPassHero'
        })
        self.assertEqual(resp.status_code, 422)

    def test_05_successful_login(self):
        """Test login with correct credentials returns valid session token and user info."""
        resp = self.client.post('/api/auth/login', json={
            'email': 'authtest_existing@example.com',
            'password': 'ValidPass123!'
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('token', data)
        self.assertIn('user', data)
        self.assertEqual(data['user']['email'], 'authtest_existing@example.com')
        self.assertEqual(data['user']['name'], 'ExistingHero')

    def test_06_login_wrong_password(self):
        """Test login with incorrect password returns 401."""
        resp = self.client.post('/api/auth/login', json={
            'email': 'authtest_existing@example.com',
            'password': 'IncorrectPassword'
        })
        self.assertEqual(resp.status_code, 401)
        data = resp.json()
        self.assertIn('Invalid email or password', data['detail'])

    def test_07_login_nonexistent_user(self):
        """Test login with non-existent email returns 401."""
        resp = self.client.post('/api/auth/login', json={
            'email': 'nonexistent_hero_ghost@example.com',
            'password': 'SomePassword123'
        })
        self.assertEqual(resp.status_code, 401)
        data = resp.json()
        self.assertIn('Invalid email or password', data['detail'])

    def test_08_authenticated_session_me(self):
        """Test /api/me succeeds with valid token and returns current user."""
        login_resp = self.client.post('/api/auth/login', json={
            'email': 'authtest_existing@example.com',
            'password': 'ValidPass123!'
        })
        token = login_resp.json()['token']

        me_resp = self.client.get('/api/me', headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(me_resp.status_code, 200)
        self.assertEqual(me_resp.json()['email'], 'authtest_existing@example.com')

    def test_09_protected_endpoint_without_token(self):
        """Test accessing protected endpoints without token returns 401."""
        resp = self.client.get('/api/me')
        self.assertEqual(resp.status_code, 401)

        dash_resp = self.client.get('/api/dashboard')
        self.assertEqual(dash_resp.status_code, 401)

    def test_10_protected_endpoint_with_invalid_token(self):
        """Test accessing protected endpoints with forged/invalid token returns 401."""
        resp = self.client.get('/api/me', headers={'Authorization': 'Bearer invalid.token.payload'})
        self.assertEqual(resp.status_code, 401)

    def test_11_logout(self):
        """Test /api/auth/logout endpoint."""
        login_resp = self.client.post('/api/auth/login', json={
            'email': 'authtest_existing@example.com',
            'password': 'ValidPass123!'
        })
        token = login_resp.json()['token']

        logout_resp = self.client.post('/api/auth/logout', headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(logout_resp.status_code, 200)
        self.assertTrue(logout_resp.json().get('ok'))
