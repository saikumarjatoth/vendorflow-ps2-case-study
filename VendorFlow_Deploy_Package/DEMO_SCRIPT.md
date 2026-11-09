# VendorFlow: five-minute demo script

This runbook is for a screen recording under five minutes. Use Chrome and keep the app full-screen. The script is narration guidance; speak naturally. No slides or video editing are needed.

## Before recording

1. Start the app with `./run.sh` and open `http://localhost:8501` in Chrome.
2. Click **Reset demo dataset** and confirm, so the sample vendor master and empty history are restored.
3. Close unrelated browser tabs and have this runbook available outside the recorded area.
4. Optional: use the supplied `demo/recording_checklist.md` to check audio and screen capture.

## 0:00–0:35 — Problem

“Vendor onboarding asks operations teams to check company and tax details, collect documents, compare bank information, and detect duplicates. Missing items and unclear name mismatches can stall payments. This demo shows a deterministic first-pass review that explains its checks and routes uncertain cases to a person.”

## 0:35–1:10 — Dashboard and intake

Show the dashboard and sample cards. Point out stored submission counts, the seeded active demo record, and the structured intake form. Say: “The samples are synthetic. The app accepts manual details and tagged document uploads; a JSON import is available as an additional path.”

## 1:10–2:10 — Successful vendor

Load **Successful Vendor**, switch to the form, and click **Submit and run review**. Let all eight stages execute. Show the identifier checks, required-document checks, bank-name comparison, duplicate lookup, final APPROVED decision and communication draft. Say: “The green outcome means the configured checks passed. It does not claim a government or bank lookup; document presence is not authenticity.”

## 2:10–3:20 — Edge case: bank-name mismatch

Return to the dashboard, load **Bank Details Mismatch**, and submit it. Show the cross-field consistency stage. Say: “The bank-holder name differs from the legal business name, so the application asks for confirmation and keeps the case PENDING. A difference alone is not labeled fraud.”

## 3:20–4:10 — Results and duplicate policy

Show the pending communication draft, then open **Run History** and inspect both runs. If time allows, run **Duplicate Vendor** after the bank-mismatch case: its exact PAN and GSTIN match the seeded active demo record, so the conservative policy rejects the duplicate record. A partial identifier match stays pending for a reviewer.

## 4:10–5:00 — Implementation choices and limits

“The core rules are deterministic and visible: normalize, validate fields, check applicable document availability, compare names, check the local vendor master, decide, and draft a message. The SQLite database preserves local run history and uploaded files. This is a demonstration workflow, not an identity or registration verification service. Email is drafted but not sent. A hosted free service may reset its filesystem; durable hosting needs persistent storage.”

## Suggested run order

For the clearest five-minute story, run **Successful Vendor**, then **Bank Details Mismatch**, then inspect **Run History**. The duplicate sample is an optional third run. Running the approved sample again after its first approval correctly matches the newly added active record, so reset before repeating the original happy path.
