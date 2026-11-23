# Regression

## Incident: the counter reset on every deploy

The app was deployed, but `DATABASE_URL` was missing.
Even so, the app kept running because `app.py` quietly used a file counter inside the container instead.
Meanwhile, `/health` returned `ok` and `/ready` showed `ready: true`, so all checks passed.
But after every redeploy, `/visits` reset to 1.
This happened because the file was saved in the container and got deleted each time the container was removed.
No one noticed the problem until the shop’s numbers were clearly off.

## The case it produced

New tests are in [`test_smoke_additional_checks.py`](./qa/test_smoke_additional_checks.py).
`test_ready_reports_postgres` now also requires `store == "postgres"` apart from `ready: true`. 
The issue now fails QA part, before the digest is written to `published.txt`.
So the failed digest does not reach the end users.
`test_visits_are_stored_in_postgres` checks the same thing on the endpoint that writes.