# Makefile pour Mon Chai V1 - Sprint 08

.PHONY: help test test-fast test-cov lint format install migrate clean

help:  ## Afficher cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Installer les dépendances
	pip install -r requirements.txt

migrate:  ## Appliquer les migrations
	python manage.py migrate

test:  ## Lancer tous les tests
	python -m pytest -v

test-fast:  ## Lancer les tests avec arrêt au premier échec
	python -m pytest --maxfail=1 --disable-warnings -q

test-cov:  ## Lancer les tests avec couverture
	python -m pytest --cov=apps --cov-report=html --cov-report=term

test-auth:  ## Lancer seulement les tests d'auth
	python -m pytest tests/test_web_auth.py -v

test-permissions:  ## Lancer seulement les tests de permissions
	python -m pytest tests/test_permissions.py -v

test-firstrun:  ## Lancer seulement les tests first-run
	python -m pytest tests/test_first_run.py -v

lint:  ## Vérifier le style de code
	ruff check .
	black --check .

format:  ## Formater le code
	black .
	ruff check --fix .

clean:  ## Nettoyer les fichiers temporaires
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage

dev-setup: install migrate  ## Configuration complète pour développement
	@echo "✅ Environnement de développement configuré"

ci-test: test-cov lint  ## Tests comme en CI
	@echo "✅ Tests CI passés"
