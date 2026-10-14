# 02 — Memory contracts and cache state

Run `python labs/run.py run memory`. Prerequisites: byte enables, synchronous requests/responses and cache geometry. Tools: Python and Icarus.

Expected checks: 500 RAM operations with masks, a retained read-first response, changing input addresses during response stalls and contents surviving protocol reset. The Python cache test compares 9000 randomized accesses with a flat byte-updated oracle, then cleans, invalidates and refills. Invalid addresses and destructive dirty invalidation are rejected.

`cache_model.py` models exact LRU and functional storage, not Wally's tree pseudo-LRU or cycle timing. Its printed example should be `direct 2 3 1` and `two-way 3 2 0` before final cleaning.

Exercise: compare conflict patterns at equal capacity. Explain hits, misses and writebacks separately; propose timing estimates only after specifying their assumptions. Change the RAM collision rule in a student variant and update its specification and checker together.
