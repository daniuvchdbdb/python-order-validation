# Validate a Small CSV Import Without Quietly Losing Bad Rows

Prepared 2 October 2026 as an original, unpublished Python writing/code sample for Hu Chengchao's applications. **The writing and code are AI-assisted.** This is a synthetic-data learning example, not a client project, prior publication, professional Python tenure or production billing system. No private data, account credentials or paid third-party service is involved.

A CSV import is deceptively easy to make look successful. Split each line on a comma, convert the amount to a float, remove repeated identifiers, and the output looks tidy. But did a quoted comma become an extra column? Did an invalid first occurrence silently prevent a later valid row from being imported? Did an amount with three decimal places get rounded without anyone agreeing to that policy?

The attached `validate_orders.py` takes a different approach: define a deliberately small contract, return evidence about rejected records, and keep all effects outside the validator. Its companion `test_validate_orders.py` exercises the contract in memory. This is a focused sample rather than a full import product or a complete Real Python-length tutorial.

## Start with the contract

Assume an agreed two-column schema: `order_id,amount`, in that exact order. An identifier is 1–64 ASCII letters, digits, underscores or hyphens; case matters. Amounts are nonnegative decimal strings with up to nine integer digits and at most two fractional digits. Surrounding whitespace in values is stripped. The first **valid** occurrence of each identifier is accepted; later valid duplicates are rejected. Bad rows remain visible as rejection records. A missing or different header, or malformed quoting, invalidates the whole input instead of returning a partial success.

These are example business rules, not universal rules for order data. Refunds, international formats, currency labels and case-insensitive identifiers may require a different contract. Obtain the client's actual schema and rejection policy before adapting this code. A negative amount might be essential in another system; guessing it away would be data loss.

## Parse the format before validating the data

The standard-library `csv.reader` understands quoted delimiters and multiline fields. Manual comma splitting does not. The validator uses `StringIO` with `newline=""` so tests can supply text without creating files. For a later file-based wrapper, Python's documentation recommends opening CSV text files with `newline=""`; encoding must also be agreed rather than guessed. This sample accepts an optional single leading Unicode BOM and an otherwise exact header. See the official [CSV reader documentation](https://docs.python.org/3/library/csv.html#csv.reader).

Using `strict=True` asks the parser to report malformed CSV it detects. It is not a claim that every conceivable CSV irregularity is rejected. Our own exact-header and field-count checks are separate, explicit protections. For example, `A,"1,000"` has two fields, not three. It passes the structural check but fails the deliberately narrow decimal policy; the rejection reason is `invalid amount`, not a misleading extra-column warning.

## Validate before deduplicating

Imagine two records with identifier `A`: the first says `wrong` for the amount, the second says `2`. Reserving the identifier before checking the amount would reject both. The implementation adds the identifier to `seen` only after every row check passes. That small ordering choice is captured by a test. Whether a first-valid-wins policy is appropriate is still a business decision: a real reconciliation workflow might instead quarantine every conflicting group.

Each result includes `source_end_line`, obtained from the reader's physical line counter. A quoted record spanning two physical lines ends on the later line. Calling this a row number would confuse someone investigating the source file, so the name makes that distinction explicit. Rejection records carry reasons, but do not copy full original values into logs. For real customer data, preserving an input file securely may be preferable to duplicating personal information across reports.

## Keep numeric normalization explicit

The amount regex rejects exponents, nonfinite values, signs, separator commas and excess fractional digits before constructing a `Decimal`. Constructing from the original validated string avoids introducing binary floating-point approximations. Formatting to two decimal places adds a trailing zero when needed; it does not silently round an accepted three-decimal input, because such an input is rejected first. The bounded length also keeps this specific formatting operation comfortably within the default decimal context. See Python's [decimal documentation](https://docs.python.org/3/library/decimal.html).

The schema's ASCII-only identifier rule also rejects formula-like identifiers beginning with `=` or `@`. This does **not** make the function a general spreadsheet-formula sanitizer. It exports no spreadsheet and accepts no arbitrary text columns. Adding descriptions or customer names would require a fresh review of destination-specific escaping and security, rather than claiming this limited check protects every export.

## Run the tests and interpret them narrowly

With Python 3.10 or newer, run in this directory:

```powershell
py -3.14 -B -m unittest discover -s . -p "test_*.py" -v
```

If your Python launcher does not have 3.14, use an installed supported interpreter instead. No package installation, network connection or database is needed. The tests cover normalization, BOM/CRLF, duplicates, rejected-first ordering, case-sensitive identifiers, missing/extra fields, schema failures, nonfinite and out-of-policy amounts, formula-like IDs, quoted commas, multiline line references, malformed quoting, blank input records and repeatable calls.

Passing these tests proves those assertions for this sample under the interpreter actually run. It does not prove production readiness, bank-grade accounting, exhaustive CSV conformance, large-file performance or successful client delivery. The validator materializes accepted and rejected records, so memory grows with input size. Its input is already decoded text: a binary-file wrapper would still need encoding, size limits, output paths, permissions and recovery behavior.

## A sensible next step

For a small paid automation task, agree on a representative anonymized sample, the exact schema and normalization rules, an acceptance example, the delivery format and a fixed fee before processing customer data. Then add file handling that never overwrites the source, a human-readable rejection report and a documented rerun command. Add each agreed edge case as a regression test. Do not describe this unfinished wrapper as an already delivered commercial import pipeline.

The most useful result is not a perfectly clean-looking file. It is a repeatable decision process that makes rejected records explainable, keeps the original recoverable and shows precisely what the tests do—and do not—establish.


## Portfolio scope

This is a self-initiated, AI-assisted learning/demo project, not a claim of commercial employment or production deployment. Private databases, credentials, local browser profiles, customer records and generated build output are excluded. Configure your own services and use synthetic data. Payment/provider integrations and deployment require independent review before production use. No new full end-to-end validation is claimed by this publication.
