Your deliverable is `out/impact.json` for the supplied Switchyard ticket. Work from the current directory and make changes only to your report and scratch scripts. Use the ticket's report requirements and `app/contracts/evidence.md` as your sources of truth.

Read the evidence contract and inspect small samples. Use a local script to parse the necessary logs and reconstruct the requested results. Cross-check sources because each can omit records. Join by stable identifiers where available. Apply the ticket's time, identity, and grouping rules. Treat shipper duplicates as described by the contract and check that observed successes are credited to the correct records.

Classify malformed rows before filtering for the incident. Count each occurrence of a corrupted row. Keep a count per file, check examples against the documented formats, and distinguish documented empty values from truncated rows. Check the report's grouping, units, totals, and JSON format. Write the report as soon as the script produces a complete result, then correct it if a check fails.

Keep tool output short and work only with the supplied evidence and contracts. Finish when the file is written and checked.
