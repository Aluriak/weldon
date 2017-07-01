
all:
	python3 problem01.py


web:
	python3 webclient.py

server:
	python3 webserver.py


t:tests
tests:
	pytest -vv --doctest-module --ignore=venv/ --ignore=run --ignore=run.backup --ignore=crypto.py --ignore=problem01_remote.py
