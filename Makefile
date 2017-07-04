
all:
	python3 problem01.py


web:
	python3 webclient.py

server:
	python3 webserver.py


t:tests
tests:
	python3 -m pytest -vv . --doctest-module --ignore=venv/ --ignore=run --ignore=run.backup --ignore=crypto.py --ignore=problem01_remote.py --ignore=gui.py
	python3 -m pytest -vv problem01.py storyline_multistudent.py
