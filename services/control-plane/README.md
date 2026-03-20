# Control Plane

Django service for source metadata and canonical playbook entries.

## Commands

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
```

### Import normalized ingestion data

```bash
python manage.py import_ingestion \
  --index-file ../../services/ingestion/output/huddle_gg_index.json \
  --plays-file ../../services/ingestion/output/huddle_gg_plays_sample.json
```

### Query playbook entries (for realtime API)

```bash
curl "http://localhost:8000/api/playbook-entries?offense_personnel=11&concepts=mesh,cross&limit=20"
```
