SHELL = /bin/bash

help:
	#pass

setup:
	docker-compose -f ./docker/docker-compose.yml build

run:
	docker-compose -f ./docker/docker-compose.yml up

stop:
	docker-compose -f ./docker/docker-compose.yml stop

tests:
	python tests.py