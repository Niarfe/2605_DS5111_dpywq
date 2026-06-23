default:
	@cat makefile

# Creates the virtual environment boundary folder structure if it doesn't exist
env:
	test -d env || python3 -m venv env
	. env/bin/activate && pip install --upgrade pip

# Chains the environment activation directly to the pip installation in one shell line
update: env
	. env/bin/activate && pip install -r requirements.txt

clean_ids:
	. env/bin/activate && cat youtube_ids | python pipeline/scripts/clean_ids.py

extract_ids:
	. env/bin/activate && cat youtube_ids | \
		python -u pipeline/scripts/clean_ids.py | \
		python -u pipeline/scripts/fetch_transcripts.py


to_sf:
	. env/bin/activate && cat youtube_ids | \
                python3 -u pipeline/scripts/clean_ids.py | \
                python3 -u pipeline/scripts/fetch_transcripts.py | \
                python3 -u pipeline/scripts/load_snowflake.py

test_enrich:
	. env/bin/activate && cat mock_transcripts.jsonl | \
                python -u bin/enrich_transcripts.py

test_to_sf:
	. env/bin/activate && cat mock_gemini_output.jsonl | python3 -u pipeline/scripts/load_snowflake.py

lint:
	@echo Fake Linter Run!

test: lint
	. env/bin/activate && pytest -vvx tests

## LECTURE 6
check_shows:
	curl -s https://talkpython.fm/episodes/rss | grep "<title>" | head -n 10

smoke_et_oop:
	echo "Astral" | python bin/extract_transcripts_oop.py --source podcast


