# Concurrency

`publish-lab-03.yml`:

    concurrency:
      group: ${{ github.workflow }}-${{ github.ref }}
      cancel-in-progress: ${{ github.event_name == 'pull_request' }}

The group is keyed on the **ref**, so each branch and each PR has its own: `publish-lab-03-refs/pull/3/merge` for the PR, `publish-lab-03-refs/heads/lab-03` for pushes.

| Run         | Event        | Commit          | Result                                    | URL                                                                                   |
|-------------|--------------|-----------------|-------------------------------------------|---------------------------------------------------------------------------------------|
| cancelled   | pull_request | 98d76f4828426541f71f512f447d6a3f540d9871 | cancelled while it was building the image | https://github.com/MarharytaFilipovych/margosha-catshop-labs/actions/runs/45186352778 |
| replaced it | pull_request | 33ffa34f66d8fe498dc45fbaf3b6e0c4f2c5de06 | success                                   | https://github.com/MarharytaFilipovych/margosha-catshop-labs/actions/runs/45186456935                                              |

### Why that was safe

A PR run publishes nothing. It builds without pushing the image to GHCR, while QA and `publish-digest` are skipped. 
The newer commit contains everything the cancelled one did, so its run gives the same answer for newer code.

### Why the publishing path is never cancelled

On `push` the `cancel-in-progress` is `false`.
Stopping a publishing run halfway could leave an image in GHCR that never went through QA, or a QA pass without `published.txt`. 
The [second push run](https://github.com/MarharytaFilipovych/margosha-catshop-labs/actions/runs/45186441126) (commit 33ffa34f66d8fe498dc45fbaf3b6e0c4f2c5de06) 
was queued behind the [first push run](https://github.com/MarharytaFilipovych/margosha-catshop-labs/actions/runs/45186335620) (commit 98d76f4828426541f71f512f447d6a3f540d9871).
It only started when the previous one had finished, which is why it took 3m 20s. Both were successful.