.PHONY: update clean_ids
default:
	@cat makefile

env:
	test -d env || python3 -m venv env
	. env/bin/activate && pip install --upgrade pip

update: env
	. env/bin/activate && pip install -r requirements.txt

clean_ids:
	. env/bin/activate && cat youtube_ids | python pipeline/scripts/clean_ids.py
