# Ingestion Service

This service contains source adapters and normalization jobs.

## Run

```bash
cd services/ingestion
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m ingestion.run
```

Note: confirm each source policy and legal constraints before production ingestion.
