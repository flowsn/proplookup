# Hetzner shared-hosting deployment notes

## Expected production shape

- static frontend under the domain web root
- Python CGI under `cgi-bin`
- PostgreSQL database with PostGIS enabled in konsoleH
- cron only for lightweight maintenance tasks
- GIS ETL executed locally or on a separate machine

## Important constraint

Do not assume a persistent ASGI/WSGI Python process on current Hetzner shared Webhosting. The portable option documented by Hetzner is Python via CGI.

A future Hetzner Cloud/VPS migration can replace CGI with FastAPI/Gunicorn/Uvicorn without changing the database schema or frontend API contract.

## Production checklist

1. Create PostgreSQL DB in konsoleH.
2. Enable PostGIS extension.
3. Import `sql/schema.sql`.
4. Upload `app/static` to web root.
5. Upload `app/cgi-bin/api.py` to CGI-enabled directory and mark executable.
6. Configure DB credentials outside public source where possible.
7. Restrict app with HTTP auth or application auth; this is a private research tool.
8. Test `/api.py/health` and parcel bbox queries.
