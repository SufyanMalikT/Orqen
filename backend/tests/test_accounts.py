from rest_framework.test import APITestCase
from apps.accounts.models import User
from rest_framework_simplejwt.tokens import RefreshToken
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

class UserLoginTest(APITestCase):
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
    

    
class UserProfileTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='Strong-Test!123'
        )

        self.refresh = RefreshToken.for_user(self.user)
        self.access_token = str(self.refresh.access_token)

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}"
        )


    def test_get_user_profile(self):
        response = self.client.get('/api/v1/users/me/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], self.user.id)

    def test_update_user_profile(self):
        response = self.client.patch(
            '/api/v1/users/me/',
            {
                'first_name':'test',
                'last_name':'user'
            },
            format='json'
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], self.user.id)

    def test_user_password_update(self):
        response = self.client.patch(
            '/api/v1/users/me/password/',
            {
                'current_password':'Strong-Test!123',
                'password':'Strong-Test!31',
                'confirm_password':'Strong-Test!31'
            }
            ,
            format='json'
        )

        self.assertEqual(response.status_code, 200)
    

    def test_user_logout(self):
        response = self.client.post(
            '/api/v1/auth/logout/',
            {
                'refresh': str(self.refresh)
            },
            format='json'
        )
        self.assertEqual(response.status_code, 205)

