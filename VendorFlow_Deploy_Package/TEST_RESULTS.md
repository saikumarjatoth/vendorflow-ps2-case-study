# VendorFlow test results

Executed **2026-11-09** in the build environment.

Command: `python -m pytest -q`

Result: **14 passed in 0.43s** (exit code 0). `python -m compileall -q app.py vendorflow tests` also completed successfully (exit code 0).

| Test case | Expected result | Actual result | Status |
| --- | --- | --- | --- |
| Successful Vendor sample through all eight stages | APPROVED | APPROVED | PASS |
| Missing Documents sample | PENDING with bank proof identified | PENDING; bank proof listed as missing | PASS |
| Bank Details Mismatch sample | PENDING for clarification | PENDING; review flag says mismatch alone is not fraud evidence | PASS |
| Duplicate Vendor sample | REJECTED for exact active PAN + GSTIN match | REJECTED; seeded record matched | PASS |
| Invalid PAN and GSTIN | PENDING | PENDING; format and PAN-consistency checks fail | PASS |
| Missing mandatory contact email and registration number | PENDING | PENDING; both required-field issues present | PASS |
| Ambiguous legal name / account-holder difference | PENDING for human review | PENDING; shared name terms remain a review item | PASS |
| One-field duplicate match | PENDING, not rejected | PENDING; possible duplicate routed to a reviewer | PASS |
| Repeat of an already approved vendor | REJECTED as a duplicate | REJECTED after the approved record enters the active master | PASS |
| Unsupported extension and mislabeled PDF | Upload validation fails | Both rejected with clear file-type/signature messages | PASS |
| Malformed JSON and normalized valid JSON | Malformed input rejected; values normalized | `ValueError` for malformed input; PAN and GST status normalized | PASS |
| Full bank account number entered | PENDING and request last four only | PENDING; account reference check fails | PASS |
| Country outside the India demo scope | PENDING | PENDING; country scope check present | PASS |
| SQLite run, document, metric and reset round trip | Data persists; reset clears runs/files and reseeds master | Assertions passed for all stored values and reset behavior | PASS |

The final local Streamlit server started on loopback; the home route returned HTTP 200 and `/_stcore/health` returned `ok`. A desktop browser visual check was not completed: the available browser automation could not access the build sandbox's loopback address. The interactive page should be opened using the included Mac startup command; no public URL has been deployed or verified.
