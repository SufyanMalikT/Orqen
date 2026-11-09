from rest_framework.test import APITestCase
from apps.accounts.models import User
class UserRegistrationTests(APITestCase):
    def test_register_user(self):
        response = self.client.post(
            "/api/v1/auth/register/",
            {
                "email":"test@example.com",
                "first_name":"test",
                "last_name":"user",
                "password":"saifi123"
        }, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            User.objects.filter(email='test@example.com').exists()
        )


    
class UserLogin(APITestCase):

    def setUp(self):
        return User.objects.create_user(
            email='test@example.com',
            password='saifi123'
        )
    def test_user_login(self):
        response = self.client.post(
        "/api/v1/auth/login/"
        ,{
            "email":"test@example.com",
            "password":"saifi123"
        }, format='json')

        self.assertEqual(response.status_code, 200)