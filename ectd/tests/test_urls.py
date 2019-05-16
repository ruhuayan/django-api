from django.urls import resolve, reverse

class TestUrls:
    
    def test_auth_url(self):
        path = reverse('auth')
        assert path == '/api-token-auth/'
        assert resolve(path).view_name == 'auth'
        # assert resolve(path).app_name == 'obtain_jwt_token'
        
    def test_register_url(self):
        pass