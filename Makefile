NOCODB_URL := http://localhost:8080
PYTHON     := python3

.PHONY: up build open down reset logs help

help:          ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

up:            ## Start NocoDB in Docker (detached)
	docker compose up -d
	@echo "Waiting for NocoDB to be healthy…"
	@until docker compose ps nocodb | grep -q "healthy"; do \
	  printf '.'; sleep 2; \
	done
	@echo
	@echo "NocoDB is ready → $(NOCODB_URL)"

build: up      ## Create schema + seed sample data (run once after 'make up')
	$(PYTHON) scripts/build_nocodb.py

open:          ## Open NocoDB in the default browser
	@xdg-open $(NOCODB_URL) 2>/dev/null || \
	  open     $(NOCODB_URL) 2>/dev/null || \
	  echo "Open $(NOCODB_URL) in your browser"

down:          ## Stop NocoDB (data volume preserved)
	docker compose down

reset:         ## Destroy containers AND data volume — full clean start
	@echo "This will permanently delete all NocoDB data."
	@read -p "Type 'yes' to confirm: " c && [ "$$c" = "yes" ]
	docker compose down -v
	@echo "Done. Run 'make build' to start fresh."

logs:          ## Tail NocoDB container logs
	docker compose logs -f nocodb
