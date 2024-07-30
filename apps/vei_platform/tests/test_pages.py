from django.test import TestCase


class ProjectTests(TestCase):
    def test_homepage(self):
        # No loging data, expect redirection to login
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        # self.assertEqual(response.url, '/accounts/login/?next=/')

    # def test_loginpage(self):
    #    response = self.client.get('/accounts/login/')
    #    self.assertEqual(response.status_code, 200)
    # self.assertEqual(response.url, '/accounts/login/?next=/')
