install:
	python -m pip install -r requirements.txt

run:
	uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

test:
	pytest

simulate:
	python run.py --seed 42 --scenario global_digital_twin

cohort:
	python scripts/run_cohort.py --size 100

compare:
	python scripts/compare_policies.py --size 100

research:
	python scripts/run_experiment.py policy-comparison --size 64
	python scripts/run_experiment.py counterfactual
	python scripts/run_experiment.py genomic-ablation --size 64
	python scripts/run_experiment.py sensitivity --samples 128
	python scripts/run_experiment.py fairness --per-group 24
	python scripts/run_experiment.py calibration --size 64

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type d -name .pytest_cache -prune -exec rm -rf {} +

world:
	python -c "from app.world import simulate_world; import json; print(json.dumps(simulate_world(42,128,12,return_trajectories=False)[\"metrics\"], indent=2))"

research-v4:
	python scripts/run_research_pack.py --seed 42
	python scripts/run_experiment.py policy-comparison --size 32
	python scripts/run_experiment.py sensitivity --samples 64
	python scripts/run_experiment.py fairness --per-group 24
	python scripts/run_experiment.py calibration --size 64

validation:
	python scripts/run_validation.py --seed 42 --seeds 4 --learners 24 --years 6

quality:
	python -m ruff check app tests scripts
	python -m mypy app
	python -m compileall -q app tests scripts
	python -m pip_audit -r requirements.txt
	python -m bandit -q -r app scripts -s B311
