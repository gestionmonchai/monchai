import json
import pytest
from django.urls import reverse
from django.test import override_settings

pytestmark = pytest.mark.django_db


def post_json(client, url, payload):
    return client.post(url, data=json.dumps(payload), content_type='application/json')


def test_get_not_allowed(client):
    url = reverse('ai:help_assistant')
    r = client.get(url)
    assert r.status_code == 405


def test_empty_message_400(client):
    url = reverse('ai:help_assistant')
    r = post_json(client, url, {"message": ""})
    assert r.status_code == 400
    assert r.json().get('error')


def test_success_200(client, monkeypatch):
    url = reverse('ai:help_assistant')

    def fake_generate(message, model=None, system=None, **kwargs):
        assert message == 'Bonjour'
        return 'Salut !'

    monkeypatch.setattr('apps.ai.views.ollama_generate', fake_generate)

    r = post_json(client, url, {"message": "Bonjour"})
    assert r.status_code == 200
    assert r.json()["answer"] == 'Salut !'


def test_rate_limit_429(client, monkeypatch):
    url = reverse('ai:help_assistant')

    def fake_generate(message, model=None, system=None, **kwargs):
        return 'ok'

    monkeypatch.setattr('apps.ai.views.ollama_generate', fake_generate)

    with override_settings(HELP_RATE_LIMIT_CALLS=1, HELP_RATE_LIMIT_WINDOW=300):
        r1 = post_json(client, url, {"message": "one"})
        assert r1.status_code == 200
        r2 = post_json(client, url, {"message": "two"})
        assert r2.status_code == 429


def test_ollama_error_502(client, monkeypatch):
    url = reverse('ai:help_assistant')

    class E(Exception):
        pass

    def fake_generate(message, model=None, system=None, **kwargs):
        from apps.ai.ollama_client import OllamaError
        raise OllamaError('down')

    monkeypatch.setattr('apps.ai.views.ollama_generate', fake_generate)

    r = post_json(client, url, {"message": "hi"})
    assert r.status_code == 502
    assert 'error' in r.json()
