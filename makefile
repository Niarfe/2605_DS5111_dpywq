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
		python pipeline/scripts/clean_ids.py | \
		python pipeline/scripts/fetch_transcripts.py
