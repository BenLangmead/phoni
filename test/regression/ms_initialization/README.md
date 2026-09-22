# Matching-statistics initialization regressions

the query initializer used zero-based select(1) while taking the reference pointer from the selected run start. When those positions differ, subsequent LF steps and LCEs operate on inconsistent state. Selecting occurrence 0 makes the BWT row agree with its run-start sample. Both in-memory and file-based query loops are repaired.

The fixtures are synthetic ACGT queries. References contain literal N separators; queries never contain N, so matches cannot cross record boundaries. The checker independently computes exact MS by substring membership and validates every reported occurrence pointer. It does not use another index implementation as its oracle.

- `toy`: 426 queries against a 455-character strand-complete reference. `GA` distinguishes the augmented-only successor-run bug: expected MS `[2, 1]`, previously `[1, 1]`.
- `seed20`: 540 queries against a different three-record collection. Its repeated leading ACGT sequence and deterministic random sequences expose inconsistent initial BWT-row/pointer state. This fixture contains every ACGT query of lengths 1–4 and 200 sampled/mutated queries.

## Run against an existing index

Build an index from the exact raw `reference.txt` for each case, using a copy in a writable working directory. With the corresponding reference/index prefix and compiled query binary:

```sh
python3 test/regression/ms_initialization/check.py \
  --binary build/test/src/phoni \
  --index /path/to/toy/reference.txt --case toy
python3 test/regression/ms_initialization/check.py \
  --binary build/test/src/phoni \
  --index /path/to/seed20/reference.txt --case seed20
```

Use the plain grammar. The augmented checker expects compressed threshold-LCE storage. The checker creates temporary query/output files, does not alter the index, returns nonzero for mismatches, and verifies that the index prefix's raw text equals the bundled fixture.

## Validation and scope

The patched query implementation passes 426/426 original queries, 5,960 expanded queries, and 540/540 queries on each of three independently generated collections. Patched PHONI and patched augmented PHONI agree with the independent oracle. The augmented file-based interface also passes 426/426. Across all passing runs, 159,204 occurrence pointers were checked against the reference text. The two bundled cases provide a compact reproduction of the initialization defects; the larger validation campaign was run separately.

The test environment used GCC 13.1.0 with `-ftrivial-auto-var-init=zero` because the existing BWT readers read five bytes into otherwise uninitialized size_t values. Missing standard-header includes in upstream/dependency code also required build compatibility workarounds. Those independent portability issues are not fixed by this branch. The preserved pre-fix augmented binary fails 29 toy queries and 123 seed20 queries in that environment; ordinary PHONI fails 93 seed20 queries. A zero-filled run number remains incorrect: it must identify the actual succeeding run.

Empty queries, absent query symbols, ambiguity semantics, and performance are outside this regression's scope. The other PHONI copies in sibling headers/repositories were not silently changed.
