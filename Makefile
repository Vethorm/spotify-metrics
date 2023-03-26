all: build up

build:
	docker compose build

up:
	docker compose up -d

lint:
	ruff check .

docstrings:
	pydocstyle --match-dir "^(?!(build)).*"

clean:
	docker compose down