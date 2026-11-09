# Public historical raw reports

These four deterministic JSON files are the exact reports exported by the original November 8 runs, now published for inspection after hosted artifacts expire. Their SHA256s match the pre-existing [summary](../AUDIT-EXECUTION-RESULTS.json); no raw report, old summary, source pin, result or assurance scope was rewritten.

| Original run/variant | Raw report | SHA256 |
| --- | --- | --- |
| Entitlement42536381195/baseline | [entitlement-cli-baseline.json](entitlement-cli-baseline.json) | d6f4f0b80672f5b7c767241708c856a371c620d172d3cbcebcfca87d75910b51 |
| Entitlement42536381195/spoof | [entitlement-cli-spoof.json](entitlement-cli-spoof.json) | f7549d5ea8d9aea78cf06227e83db6dbe8592768cc68c8e45952ebc6239ef914 |
| External42537171457/baseline | [external-json-baseline.json](external-json-baseline.json) | 1496a5cb5058390caea174d8c8834c40e4fa9e5502135554c23a42357ad7213a |
| External42537171457/mutation | [external-json-mutation.json](external-json-mutation.json) | 183f05d5436c793557044cb4a4cef8640e936d88c8406a7419d6f58225a51f6c |

Publication review found public synthetic tenant fixtures/published identifier examples, logical source names, digests and finite observations only. Reports contain no candidate stderr, credentials, provider/session logs, customer records or raw host environment/configuration values. No redaction was necessary, so exact original bytes and hashes are preserved. The upstream implementation itself is not included in these reports.

The external reports used schema 1 with a candidate-controlled shim. Their passing fixture agreement does **not** establish execution of the intended Luhn function; see [issue41](https://github.com/deveshkakkar/ProofGate/issues/41). Later driver pinning does not strengthen these historical observations. Files allow independent recalculation of the recorded finite outcomes and consistency receipts, not independent authentication of original execution or a new formal proof. Hosted ZIP/log provenance remains separately cited, potentially ephemeral evidence. Producer authentication, policy admission, developer adoption and release authority are not established.
