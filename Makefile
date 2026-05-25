# Variables
ENV_FILE = .env
DOCKER_DIR = app


# ─────────────────────────────────────
#  Docker
# ─────────────────────────────────────

up:
	cd $(DOCKER_DIR) && docker-compose --env-file ../$(ENV_FILE) up 

down:
	cd $(DOCKER_DIR) && docker-compose --env-file ../$(ENV_FILE) down

restart:
	cd $(DOCKER_DIR) && docker-compose --env-file ../$(ENV_FILE) restart

build:
	cd $(DOCKER_DIR) && docker-compose --env-file ../$(ENV_FILE) up --build

build_no_cache:
	cd $(DOCKER_DIR) && docker-compose --env-file ../$(ENV_FILE) build --no-cache
	cd $(DOCKER_DIR) && docker-compose --env-file ../$(ENV_FILE) up

logs-db:
	docker logs -f flight_predictor_db


# ─────────────────────────────────────
#  ETL
# ─────────────────────────────────────

etl-bronze:
	cd ETL && python3 main_bronze_async.py

etl-silver:
	cd ETL && python3 main_silver_async.py

etl-gold:
	cd DBT && dbt run --select tag:staging_init && dbt run --select tag:gold_init


# ─────────────────────────────────────
#  Nettoyage
# ─────────────────────────────────────

clean:
	cd $(DOCKER_DIR) && docker-compose --env-file ../$(ENV_FILE) down -v
	docker network prune -f
	docker container prune -f

run-full: etl-bronze etl-silver etl-gold


# ─────────────────────────────────────
#  Aide
# ─────────────────────────────────────

help:
	@echo "╔════════════════════════════════════════╗"
	@echo "║         Commandes disponibles          ║"
	@echo "╠════════════════════════════════════════╣"
	@echo "║ make up          → Lancer Docker       ║"
	@echo "║ make logs-db     → Voir les logs db    ║"
	@echo "║ make etl-bronze  → Lancer ETL Bronze   ║"
	@echo "║ make etl-silver  → Lancer ETL Silver   ║"
	@echo "║ make etl-gold    → Lancer ETL Gold     ║"
	@echo "║ make run-full    → Lancer ETL Full     ║"
	@echo "║ make clean       → Tout nettoyer       ║"
	@echo "╚════════════════════════════════════════╝"
