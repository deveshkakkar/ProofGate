# Reservation authority validation

Engineering controls are distinct from activated protected authority. No live
producer signature was issued, environment/protection changed, or candidate admitted.
Historical Bend and Lean receipts retain their original provenance.

| Control | Layer / evidence | Acceptance still needed |
| --- | --- | --- |
| Valid reservation | Real unchanged Lean/kernel/nanoda/native build, 11,716 bridge cases, seven HTTP groups through new producer; API/adoption substituted | Protected hosted producer and consumer under adopted root |
| Consistent forged passing rows | Fixture validates internal hashes then is denied at authentication; real pinned CLI also rejects the fabricated ZIP against an unrelated genuine signature | Actual adversarial protected-platform run |
| Candidate policy/evaluator/workflow replacement | Input selection denies paths outside three candidate files; immutable base/head compare avoids mutable PR-files A/B/A join | Platform principal cannot edit adopted tag/environment/workflow |
| Replaced artifact, receipt, log, source or handoff | Bundle inventory/hash/receipt checks; independent expected handoff SHA; real CLI denies modified signed artifact | Protected signing workflow activation |
| Wrong signer/workflow/revision/repository/run/runner | Fixed CLI flags + verified certificate unit controls; genuine upstream signature with wrong workflow rejected by real CLI | Actual ProofGate signer/workflow identity |
| Stale head/base/policy, rerun or wrong requested PR | Independent GET checks before publication; fixture controls deny stale/revoked/replayed identity | Server-side merge eligibility/epoch and atomic freshness remain pending |
| Missing/invalid authentication | Failure before ZIP parsing; actual CLI rejects invalid signature input | Authority availability under activated configuration |
| Positive cryptography | Real pinned gh2.105.0 verifies fixed public CLI fixture using default roots | This fixture is NOT a ProofGate producer |

Commands (run from reviewed checkout; output directories must be new):

```sh
python3 -B lean4/authority/test_authority.py -v
python3 -B lean4/authority/bootstrap_gh.py --output /OWNER_CONTROLLED/authority-gh
python3 -B lean4/authority/check_crypto.py --gh /OWNER_CONTROLLED/authority-gh \
  --fixtures /OWNER_CONTROLLED/public-fixtures --output /OWNER_CONTROLLED/crypto-controls.json
python3 -B lean4/authority/check_local.py --output /OWNER_CONTROLLED/local-producer-control
```

The pinned CLI exposes aggregate `verifying with issuer` errors for wrong signer
and subject. Each negative is followed by the genuine positive; failure of any
positive makes the entire control fail. The CLI's inner reason remains unexposed,
so those results are recorded as cryptographic rejections of controlled changes,
not separately inspected inner crypto diagnostics. Fixture contract tests identify
the exact admission rejection layer. Missing tools/crashes/timeouts are failures,
never accepted negative-control evidence.

The ordinary `Protected authority engineering controls` PR workflow runs these
same controls on a disposable hosted runner with read-only permissions. It never
calls the protected dispatch workflow or acquires OIDC/signing permission. The
existing migration CI runs under its unchanged trigger; it remains ordinary CI.

## Independent engineering review

A separate fresh-context code review inspected the production writer, signature
boundary, strict consumer and workflows. It identified a mutable PR-files join
and a wrong pinned download-action handoff path. Both were corrected before
publication: immutable `compare/{base}...{head}` with identity checks and an A/B/A
regression; explicit `merge-multiple:true` and a single root handoff path.
This is engineering review, not another review of the historical Photon candidate.
Exact final tested revision, result identities and CI links are recorded in the PR.

## Live acceptance remains open

V01–V04/V06 have implemented fail-closed paths and engineering controls, not live
protected acceptance. V05 server-enforced merge freshness is not implemented by
this artifact consumer. V07 candidate isolation reuses the fixed evaluator; full
restricted-principal/canary authority acceptance retains its separate outstanding
Axx rows. A13/A14 evidence is not manufactured from a local test.

Human policy adoption, protected producer tag/environment, actual protected
positive/adversarial runs and owner-controlled result consumption remain missing.
Any future automatic merge/check integration needs its own reviewed server-side
eligibility boundary. No claim that an identical check name, ordinary green CI,
a self-consistent row, an old merge, a static review or a smoke authenticates
policy admission is made.
