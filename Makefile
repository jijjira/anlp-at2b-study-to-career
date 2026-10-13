# Shortcuts (Mac/Linux; on Windows run the commands by hand or use the .bat launchers).
.PHONY: install test app clean

install:
	python -m pip install -r requirements.txt

test:
	cd step3_baseline_nlp && python -m pytest -q
	cd step4_semantic && python -m pytest -q
	cd step5_matching && python -m pytest -q

app:
	python -m streamlit run step6_app/app.py

clean:
	find . -name __pycache__ -o -name .pytest_cache -o -name .ipynb_checkpoints | xargs rm -rf
