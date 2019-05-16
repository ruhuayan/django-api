from mixer.backend.django import mixer
import pytest

@pytest.mark.django_db
class TestModels:

    def test_template(self): 
        template = mixer.blend('applications.Template', name = 'test')
        assert template.destination == 'CN'