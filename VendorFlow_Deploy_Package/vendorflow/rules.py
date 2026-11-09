"""Deterministic vendor onboarding checks with a reviewable audit trail."""

from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime, timezone
from email.utils import parseaddr
from pathlib import Path
from typing import Any, Iterable, Iterator


FIELDS = (
    "legal_name",
    "trading_name",
    "entity_type",
    "country",
    "registration_number",
    "contact_email",
    "contact_phone",
    "pan",
    "gst_status",
    "gstin",
    "bank_account_holder",
    "account_last4",
    "ifsc",
)

FIELD_LABELS = {
    "legal_name": "Legal business name",
    "trading_name": "Trading name",
    "entity_type": "Entity type",
    "country": "Country",
    "registration_number": "Business registration number",
    "contact_email": "Contact email",
    "contact_phone": "Contact number",
    "pan": "PAN",
    "gst_status": "GST registration status",
    "gstin": "GSTIN",
    "bank_account_holder": "Bank account holder name",
    "account_last4": "Account last four digits",
    "ifsc": "IFSC",
}

DOCUMENT_LABELS = {
    "pan_proof": "PAN supporting document",
    "gst_certificate": "GST registration document",
    "bank_proof": "Bank proof",
    "business_registration": "Business registration document",
    "other": "Other compliance document",
}

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".docx", ".xlsx", ".txt", ".csv"}
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
LEGAL_SUFFIXES = {
    "private", "limited", "pvt", "ltd", "llp", "inc", "incorporated",
    "company", "co", "corporation", "corp", "the", "and",
}


def normalize_text(value: Any) -> str:
    """Trim and collapse whitespace without changing a person's/business name."""
    if value is None:
        return ""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", str(value))).strip()


def normalize_vendor(vendor: dict[str, Any]) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for key in FIELDS:
        value = normalize_text(vendor.get(key, ""))
        if key in {"pan", "gstin", "ifsc"}:
            value = re.sub(r"\s+", "", value).upper()
        elif key == "gst_status":
            status = value.lower().replace(" ", "_")
            if status in {"registered", "yes", "true"}:
                value = "registered"
            elif status in {"not_registered", "unregistered", "no", "false", "not_applicable"}:
                value = "not_registered"
            else:
                value = status
        normalized[key] = value
    return normalized


def parse_vendor_json(raw: str) -> dict[str, str]:
    """Parse a JSON object, accepting either a root vendor object or {vendor:{...}}."""
    try:
        value = json.loads(raw)
    except (json.JSONDecodeError, TypeError) as exc:
        raise ValueError(f"Invalid JSON: {exc.msg if isinstance(exc, json.JSONDecodeError) else 'expected text'}") from exc
    if not isinstance(value, dict):
        raise ValueError("JSON must contain an object of vendor fields.")
    if "vendor" in value:
        value = value["vendor"]
    if not isinstance(value, dict):
        raise ValueError("The 'vendor' value must be a JSON object.")
    unknown = sorted(set(value) - set(FIELDS))
    if unknown:
        raise ValueError("Unknown vendor field(s): " + ", ".join(unknown))
    return normalize_vendor({key: value.get(key, "") for key in FIELDS})


def _check(check_id: str, label: str, status: str, message: str) -> dict[str, str]:
    return {"id": check_id, "label": label, "status": status, "message": message}


def validate_vendor_fields(v: dict[str, str]) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []
    required = ["legal_name", "entity_type", "country", "contact_email", "contact_phone", "pan",
                "gst_status", "bank_account_holder", "account_last4", "ifsc"]
    if v.get("entity_type") in {"Private Limited Company", "Public Limited Company", "LLP", "Partnership"}:
        required.append("registration_number")
    for field in required:
        if not v.get(field, "").strip():
            checks.append(_check(f"required_{field}", FIELD_LABELS[field], "issue",
                                 f"{FIELD_LABELS[field]} is required. Add it to the submission."))
    if v.get("country") and v["country"].strip().lower() != "india":
        checks.append(_check("country_scope", "Country scope", "issue",
                             "This demonstration validates India-based vendors only. Select India or use an India-specific onboarding workflow."))
    for field in ("trading_name", "gstin"):
        if field not in required and not v.get(field, "").strip():
            checks.append(_check(f"optional_{field}", FIELD_LABELS[field], "pass",
                                 f"{FIELD_LABELS[field]} is optional for this submission."))

    pan = v.get("pan", "").upper()
    pan_ok = bool(re.fullmatch(r"[A-Z]{5}[0-9]{4}[A-Z]", pan))
    checks.append(_check("pan_format", "PAN format", "pass" if pan_ok else "issue",
                         "PAN matches the expected 10-character format." if pan_ok
                         else "PAN must contain five letters, four digits and one letter (for example ABCDE1234F). Correct the PAN."))

    email = v.get("contact_email", "")
    parsed_email = parseaddr(email)[1]
    email_ok = parsed_email == email and bool(re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email))
    checks.append(_check("email_format", "Contact email format", "pass" if email_ok else "issue",
                         "Email has a recognizable address format." if email_ok
                         else "Enter an email address in name@example.com format."))

    digits = re.sub(r"\D", "", v.get("contact_phone", ""))
    phone_ok = len(digits) >= 10
    checks.append(_check("phone_format", "Contact number", "pass" if phone_ok else "issue",
                         "Contact number contains at least 10 digits." if phone_ok
                         else "Enter a contact number with at least 10 digits."))

    if v.get("gst_status") == "registered":
        gstin = v.get("gstin", "").upper()
        gst_ok = bool(re.fullmatch(r"[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]", gstin))
        checks.append(_check("gstin_format", "GSTIN format", "pass" if gst_ok else "issue",
                             "GSTIN matches the expected 15-character structure." if gst_ok
                             else "A registered vendor needs a 15-character GSTIN in the expected format. Correct the GSTIN."))
        pan_match = gst_ok and pan_ok and gstin[2:12] == pan
        checks.append(_check("gstin_pan_consistency", "PAN within GSTIN", "pass" if pan_match else "issue",
                             "The PAN portion of GSTIN matches the submitted PAN." if pan_match
                             else "The PAN embedded in GSTIN must match the submitted PAN. Correct one of the identifiers."))
    elif v.get("gst_status") == "not_registered":
        checks.append(_check("gst_status", "GST registration status", "pass",
                             "Vendor is marked as not registered; a GSTIN and GST certificate are not required."))
    elif v.get("gst_status"):
        checks.append(_check("gst_status", "GST registration status", "issue",
                             "Choose Registered or Not registered for GST status."))

    if v.get("gst_status") != "registered" and v.get("gstin"):
        checks.append(_check("gstin_unexpected", "GSTIN applicability", "issue",
                             "A GSTIN was supplied while status is not Registered. Confirm the status or remove GSTIN."))

    if v.get("account_last4") and not re.fullmatch(r"[0-9]{4}", v["account_last4"]):
        checks.append(_check("account_last4", "Bank account reference", "issue",
                             "Enter only the final four account digits; do not submit a full account number."))
    elif v.get("account_last4"):
        checks.append(_check("account_last4", "Bank account reference", "pass",
                             "Only four account digits are present; the full account number is not collected."))

    if v.get("ifsc"):
        ifsc_ok = bool(re.fullmatch(r"[A-Z]{4}0[A-Z0-9]{6}", v["ifsc"].upper()))
        checks.append(_check("ifsc_format", "IFSC format", "pass" if ifsc_ok else "issue",
                             "IFSC matches the expected 11-character structure." if ifsc_ok
                             else "Enter an 11-character IFSC in four letters, zero, then six alphanumeric characters."))
    return checks


def expected_document_types(v: dict[str, str]) -> set[str]:
    expected = {"pan_proof", "bank_proof"}
    if v.get("gst_status") == "registered":
        expected.add("gst_certificate")
    if v.get("entity_type") in {"Private Limited Company", "Public Limited Company", "LLP", "Partnership"}:
        expected.add("business_registration")
    return expected


def validate_document_file(filename: str, content: bytes) -> tuple[bool, str]:
    """Check an upload's extension, size, and basic file signature; never authenticity."""
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        return False, f"{filename}: file type is not supported. Use PDF, PNG, JPG, DOCX, XLSX, TXT or CSV."
    if not content:
        return False, f"{filename}: the file is empty. Upload a non-empty file."
    if len(content) > MAX_UPLOAD_BYTES:
        return False, f"{filename}: file exceeds the 10 MB per-file limit."
    valid_signature = True
    if suffix == ".pdf":
        valid_signature = content.startswith(b"%PDF-")
    elif suffix == ".png":
        valid_signature = content.startswith(b"\x89PNG\r\n\x1a\n")
    elif suffix in {".jpg", ".jpeg"}:
        valid_signature = content.startswith(b"\xff\xd8\xff")
    elif suffix in {".docx", ".xlsx"}:
        valid_signature = content.startswith(b"PK\x03\x04")
    elif suffix in {".txt", ".csv"}:
        try:
            content.decode("utf-8")
        except UnicodeDecodeError:
            valid_signature = False
    if not valid_signature:
        return False, f"{filename}: file contents do not match its {suffix[1:].upper()} file extension. Upload a valid file."
    return True, "File type and basic signature accepted; content and authenticity are not independently verified."


def _name_tokens(value: str) -> set[str]:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii").lower()
    tokens = set(re.findall(r"[a-z0-9]+", value)) - LEGAL_SUFFIXES
    return tokens


def compare_account_name(legal_name: str, holder_name: str) -> tuple[str, str]:
    legal, holder = _name_tokens(legal_name), _name_tokens(holder_name)
    if not legal or not holder:
        return "issue", "Legal business name and bank account holder are both required for comparison. Add the missing name."
    shared = legal & holder
    if legal == holder:
        return "pass", "Bank account holder matches the business name after removing legal suffixes and punctuation."
    if shared:
        return "review", "The names share some words but are not an exact normalized match. Confirm that the account belongs to this vendor."
    return "review", "The submitted bank account holder name differs from the legal business name. Request confirmation or bank proof review; a name difference alone is not evidence of fraud."


def find_duplicate(v: dict[str, str], vendor_master: Iterable[dict[str, Any]]) -> dict[str, Any]:
    active = [row for row in vendor_master if row.get("status", "active") == "active"]
    for row in active:
        same_pan = bool(v.get("pan") and v["pan"] == row.get("pan", ""))
        same_gstin = bool(v.get("gstin") and v["gstin"] == row.get("gstin", ""))
        if same_pan and same_gstin:
            return {"kind": "confirmed", "record_id": row.get("record_id", "existing record"),
                    "legal_name": row.get("legal_name", "Existing vendor")}
    for row in active:
        same_pan = bool(v.get("pan") and v["pan"] == row.get("pan", ""))
        same_gstin = bool(v.get("gstin") and v["gstin"] == row.get("gstin", ""))
        same_name = (_name_tokens(v.get("legal_name", "")) == _name_tokens(row.get("legal_name", ""))
                     and bool(_name_tokens(v.get("legal_name", ""))))
        if same_pan or same_gstin or same_name:
            return {"kind": "possible", "record_id": row.get("record_id", "existing record"),
                    "legal_name": row.get("legal_name", "Existing vendor")}
    return {"kind": "none"}


def build_communication(decision: str, vendor: dict[str, str], reasons: list[str], next_action: str) -> dict[str, str]:
    name = vendor.get("trading_name") or vendor.get("legal_name") or "Vendor"
    if decision == "APPROVED":
        subject = f"Vendor onboarding review complete — {name}"
        body = (f"Hello {name},\n\nYour onboarding submission has passed the configured completeness and format checks. "
                "Your vendor onboarding review is approved for the next internal setup step.\n\n"
                "This review checks submitted information and document availability; it does not independently verify government registrations or bank ownership.\n\nRegards,\nVendor Operations")
    elif decision == "REJECTED":
        subject = f"Action required: duplicate vendor submission — {name}"
        body = (f"Hello {name},\n\nWe could not create a second vendor record because the submitted PAN and GSTIN both match an existing active vendor record. "
                "Please contact Vendor Operations if this submission represents a distinct legal entity or the existing record should be corrected.\n\n"
                "No fraud conclusion has been made.\n\nRegards,\nVendor Operations")
    else:
        subject = f"Information needed to complete vendor onboarding — {name}"
        items = "\n".join(f"• {reason}" for reason in reasons) or "Please confirm the flagged details with Vendor Operations."
        body = (f"Hello {name},\n\nWe have received your vendor onboarding submission. We need the following information or clarification before we can complete our review:\n\n"
                f"{items}\n\n{next_action}\n\nPlease reply with the requested details or documents.\n\nRegards,\nVendor Operations")
    return {"subject": subject, "body": body, "delivery": "Draft only — no email was sent."}


def review_vendor(vendor: dict[str, Any], documents: list[dict[str, Any]],
                  vendor_master: Iterable[dict[str, Any]]) -> Iterator[dict[str, Any]]:
    """Run each real decision stage and yield its result as soon as the stage completes."""
    received_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    yield {"number": 1, "key": "received", "title": "Submission received", "state": "pass",
           "message": f"Submission received at {received_at} UTC. {len(documents)} supporting file(s) attached.",
           "checks": [], "vendor": vendor}

    v = normalize_vendor(vendor)
    yield {"number": 2, "key": "normalization", "title": "Information normalisation", "state": "pass",
           "message": "Whitespace collapsed; PAN, GSTIN and IFSC standardised to uppercase.",
           "checks": [_check("normalize", "Normalized fields", "pass", "Input values are normalized before comparison.")],
           "vendor": v}

    field_checks = validate_vendor_fields(v)
    yield {"number": 3, "key": "field_validation", "title": "Field validation", "state": "issue" if any(c["status"] == "issue" for c in field_checks) else "pass",
           "message": f"{sum(c['status'] == 'pass' for c in field_checks)} checks passed; {sum(c['status'] == 'issue' for c in field_checks)} need correction.",
           "checks": field_checks, "vendor": v}

    attached_types = {doc.get("doc_type") for doc in documents if doc.get("valid", True)}
    expected = expected_document_types(v)
    missing = sorted(expected - attached_types)
    document_checks = [_check(f"document_{kind}", DOCUMENT_LABELS[kind], "issue" if kind in missing else "pass",
                              f"Missing {DOCUMENT_LABELS[kind]}. Attach it to continue." if kind in missing
                              else f"{DOCUMENT_LABELS[kind]} is attached; availability only, authenticity is not verified.")
                       for kind in sorted(expected)]
    invalid_uploads = [doc for doc in documents if not doc.get("valid", True)]
    document_checks.extend(_check("invalid_upload_" + str(i), "Upload file check", "issue", doc.get("error", "A supporting file is invalid."))
                           for i, doc in enumerate(invalid_uploads, 1))
    yield {"number": 4, "key": "documents", "title": "Document completeness", "state": "issue" if missing or invalid_uploads else "pass",
           "message": f"{len(expected) - len(missing)} of {len(expected)} applicable document types attached; {len(invalid_uploads)} invalid file(s).",
           "checks": document_checks, "expected_documents": sorted(expected), "missing_documents": missing}

    name_status, name_message = compare_account_name(v.get("legal_name", ""), v.get("bank_account_holder", ""))
    consistency_checks = [_check("bank_name", "Legal name vs bank holder", name_status, name_message)]
    yield {"number": 5, "key": "consistency", "title": "Cross-field consistency", "state": "issue" if name_status != "pass" else "pass",
           "message": "Name comparison is deterministic and conservative; uncertain cases go to human review.",
           "checks": consistency_checks}

    duplicate = find_duplicate(v, vendor_master)
    if duplicate["kind"] == "confirmed":
        duplicate_check = _check("duplicate_confirmed", "Vendor master match", "issue",
                                 f"PAN and GSTIN both match active vendor record {duplicate['record_id']} ({duplicate['legal_name']}). Confirmed duplicate under the demo policy.")
    elif duplicate["kind"] == "possible":
        duplicate_check = _check("duplicate_possible", "Vendor master match", "review",
                                 f"A PAN, GSTIN or normalized legal-name match was found in record {duplicate['record_id']} ({duplicate['legal_name']}). Route to a human reviewer; do not reject on this partial match.")
    else:
        duplicate_check = _check("duplicate_none", "Vendor master match", "pass", "No matching active vendor record was found in the local demo master.")
    yield {"number": 6, "key": "duplicates", "title": "Duplicate detection", "state": "issue" if duplicate["kind"] == "confirmed" else "review" if duplicate["kind"] == "possible" else "pass",
           "message": duplicate_check["message"], "checks": [duplicate_check], "duplicate": duplicate}

    all_checks = field_checks + document_checks + consistency_checks + [duplicate_check]
    issues = [c["message"] for c in all_checks if c["status"] in {"issue", "review"}]
    if duplicate["kind"] == "confirmed":
        decision = "REJECTED"
        next_action = f"Do not create a second vendor record. Ask Vendor Operations to reconcile record {duplicate['record_id']} if the vendor disputes the match."
        reasons = [duplicate_check["message"]]
    elif issues:
        decision = "PENDING"
        next_action = "Vendor Operations should review the flagged fields and request the listed corrections or documents before approval."
        reasons = issues
    else:
        decision = "APPROVED"
        next_action = "Vendor may proceed to the standard internal procurement and payables setup step."
        reasons = ["All configured mandatory fields and documents are present; format checks pass; no unresolved consistency issue or duplicate was found in the local demo master."]
    yield {"number": 7, "key": "decision", "title": "Decision generation", "state": "issue" if decision != "APPROVED" else "pass",
           "message": f"{decision}: {reasons[0]}", "checks": [_check("final_decision", decision.title(), "pass" if decision == "APPROVED" else "issue", reasons[0])],
           "decision": decision, "reasons": reasons, "next_action": next_action, "vendor": v}

    communication = build_communication(decision, v, reasons, next_action)
    yield {"number": 8, "key": "communication", "title": "Communication preparation", "state": "pass",
           "message": "A review-ready communication draft is prepared; nothing is sent.",
           "checks": [_check("communication", "Vendor communication", "pass", "Draft generated for human review; delivery is not configured.")],
           "decision": decision, "reasons": reasons, "next_action": next_action,
           "communication": communication, "vendor": v, "duplicate": duplicate,
           "checks_all": all_checks, "received_at": received_at}


def demo_document_bytes(doc_type: str, case_id: str) -> tuple[str, bytes]:
    """Read an openly labeled synthetic placeholder; never an official-looking proof."""
    filename = f"{doc_type}__demo.txt"
    path = Path(__file__).resolve().parent.parent / "demo" / "sample_documents" / filename
    if not path.exists():
        content = f"DEMONSTRATION ONLY\nCase: {case_id}\nDocument type: {doc_type}\nSynthetic availability placeholder; not a real document.\n"
        return filename, content.encode("utf-8")
    return filename, path.read_bytes()

