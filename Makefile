.PHONY: run dashboard evaluate slack-update

run:
	python3 -m src.main

dashboard:
	STREAMLIT_BROWSER_GATHER_USAGE_STATS=false streamlit run dashboard/app.py --server.headless true

evaluate:
	python3 -m src.evaluate

slack-update:
	python3 -m src.slack_mock
