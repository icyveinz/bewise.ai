.ONESHELL:

up:
	cls
	docker-compose up --build

cleaned:
	cls
	docker system prune -a -f
	docker-compose up --build