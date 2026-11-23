# CACHE

Measured on the pull-request path -> only build and test.
A PR run publishes nothing, so QA and `publish-digest` parts are skipped.
The first run of PR started cold, because a PR run can only read caches from its own ref and from `main`, and both were empty.

| run | caches | duration | URL |
|---|---|---|---|
| cold | none (pip cache not found, image build 0% cached) | 76s | https://github.com/MarharytaFilipovych/margosha-catshop-labs/actions/runs/45181829991 |
| warm | pip cache exact hit, image build 50% cached | 56s | https://github.com/MarharytaFilipovych/margosha-catshop-labs/actions/runs/45182366209 |

**Saved: 20s, 26% faster.**

## Which cache did which work

**Layer cache** (`cache-from/cache-to: type=gha,mode=max`): the image build went from 11s to 4s, and the `image` job from 31s to 20s. 
The `pip install` layer came back from cache because the Dockerfile copies `requirements.txt` and installs before `COPY app.py`.

**Dependency cache** (`actions/cache`, key `pip-Linux-3.12-<hashFiles(lab-03/requirements*.txt)>`): 
the warm run's `pip install` puts "Using cached" for every package, but the install-and-test step only went from 11s to 8s. 
The dependencies are too small, so it took almost the same time. 

The layer cache did the work.

The same comparison on push runs (with QA and `publish-digest`) was 144s against 126s, which is only 12% faster.
That's because most of the time in those runs (Postgres start-up, stack teardown, job start-up) does not depend on any cache.