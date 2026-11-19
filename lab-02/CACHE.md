# Cache

I have two caches: pip downloads (`actions/setup-python`, `cache: pip`, keyed on a hash of the requirements files)
and Docker layers (`docker/build-push-action`, `cache-to: type=gha,mode=max`, each layer keyed on its
instruction and inputs).

It was with the same commit (`c316db2`).
Every cache was deleted before the cold run, then I pressed the button **Re-run all jobs**.

| Step                                          | Cold | Warm |
|-----------------------------------------------|---|---|
| test -> Install the required dependencies     | 6s | 4s |
| publish -> Build the image for the smoke test | 18s | 8s |

- Cold: https://github.com/MarharytaFilipovych/margosha-catshop-labs/actions/runs/44559299276/attempts/2
- Warm: https://github.com/MarharytaFilipovych/margosha-catshop-labs/actions/runs/44559299276/attempts/3

The Docker build time was cut because the base image and the `pip install` layer were restored from the GitHub Actions
cache. So, they did not have to be downloaded and rebuilt again.
