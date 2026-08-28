SHELL := /bin/sh

.PHONY: init up down restart ps logs validate smoke clean

init:
	@test -f .env || cp .env.example .env
	@echo "Created .env. Change the default passwords before production use."

up: init
	docker compose up -d

down:
	docker compose down

restart:
	docker compose restart

ps:
	docker compose ps

logs:
	docker compose logs -f --tail=200

validate:
	docker compose config --quiet
	./scripts/validate.sh

smoke:
	./scripts/smoke-test.sh

clean:
	docker compose down -v

