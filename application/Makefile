HOST ?= localhost
PORT ?= 8001

run:
	uvicorn main:app --host ${HOST} --port ${PORT} --reload
generate:
	pip freeze > requirements.txt
check:
	ruff check . --fix