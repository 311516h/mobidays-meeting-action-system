.PHONY: run dashboard

run:
	python3 -m src.main

dashboard:
	STREAMLIT_BROWSER_GATHER_USAGE_STATS=false streamlit run dashboard/app.py --server.headless true
