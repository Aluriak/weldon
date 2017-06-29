
all:
	python3 problem01.py


web:
	python3 webclient.py

server:
	python3 webserver.py


t:tests
tests:
	pytest -vv test/
