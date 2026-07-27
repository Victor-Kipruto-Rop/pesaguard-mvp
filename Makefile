gateway-test:
	cd gateway && python3.13 -m pytest tests

gateway-run:
	cd gateway && python3.13 -m uvicorn app.main:app --reload
