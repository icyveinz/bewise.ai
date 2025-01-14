.ONESHELL:

up:
	cls
	docker-compose up --build

cleaned:
	cls
	docker system prune -a -f
	docker-compose up --build

push:
	cls
	git add .
	git commit -m "$(msg)"
	git push -u origin main