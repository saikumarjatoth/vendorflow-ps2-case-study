from __future__ import annotations

import hashlib

from vendorflow.rules import (
    demo_document_bytes,
    find_duplicate,
    parse_vendor_json,
    review_vendor,
    validate_document_file,
)
from vendorflow.samples import SEEDED_VENDORS, SAMPLES, get_sample


def docs_for(case_id: str) -> list[dict]:
    result = []
    for doc_type in SAMPLES[case_id]["documents"]:
        filename, content = demo_document_bytes(doc_type, case_id)
        result.append({"doc_type": doc_type, "filename": filename, "content": content,
                       "sha256": hashlib.sha256(content).hexdigest(), "valid": True})
    return result


def run_sample(case_id: str, master=None):
    sample = get_sample(case_id)
    stages = list(review_vendor(sample["vendor"], docs_for(case_id), master if master is not None else SEEDED_VENDORS))
    result = stages[-1]
    result["stages"] = stages
    return result


def test_all_four_samples_use_the_real_decision_engine():
    for case_id, sample in SAMPLES.items():
        result = run_sample(case_id)
        assert result["decision"] == sample["expected"]
        assert [stage["number"] for stage in result["stages"]] == list(range(1, 9))
        assert len(result["checks_all"]) > 0
        assert len(result["reasons"]) > 0
        assert result["communication"]["delivery"] == "Draft only — no email was sent."


def test_invalid_pan_and_gstin_are_pending():
    sample = get_sample("success")
    sample["vendor"]["pan"] = "INVALID"
    sample["vendor"]["gstin"] = "00INVALID"
    result = list(review_vendor(sample["vendor"], docs_for("success"), SEEDED_VENDORS))[-1]
    failed = {check["id"] for check in result["checks_all"] if check["status"] == "issue"}
    assert result["decision"] == "PENDING"
    assert {"pan_format", "gstin_format", "gstin_pan_consistency"} <= failed


def test_missing_required_information_is_pending():
    sample = get_sample("success")
    sample["vendor"]["contact_email"] = ""
    sample["vendor"]["registration_number"] = ""
    result = list(review_vendor(sample["vendor"], docs_for("success"), SEEDED_VENDORS))[-1]
    failed = {check["id"] for check in result["checks_all"] if check["status"] == "issue"}
    assert result["decision"] == "PENDING"
    assert {"required_contact_email", "required_registration_number"} <= failed


def test_missing_document_sample_is_pending_with_exact_action():
    result = run_sample("missing_docs")
    missing = next(stage for stage in result["stages"] if stage["key"] == "documents")
    assert result["decision"] == "PENDING"
    assert missing["missing_documents"] == ["bank_proof"]
    assert any("Bank proof" in reason for reason in result["reasons"])


def test_obvious_bank_name_mismatch_is_pending_not_rejected():
    result = run_sample("bank_mismatch")
    assert result["decision"] == "PENDING"
    bank_check = next(check for check in result["checks_all"] if check["id"] == "bank_name")
    assert bank_check["status"] == "review"
    assert "not evidence of fraud" in bank_check["message"]


def test_ambiguous_bank_name_difference_is_human_review():
    sample = get_sample("success")
    sample["vendor"]["legal_name"] = "Cedar Data Solutions Private Limited"
    sample["vendor"]["bank_account_holder"] = "Cedar Digital Solutions Pvt Ltd"
    result = list(review_vendor(sample["vendor"], docs_for("success"), SEEDED_VENDORS))[-1]
    check = next(item for item in result["checks_all"] if item["id"] == "bank_name")
    assert check["status"] == "review"
    assert result["decision"] == "PENDING"


def test_partial_duplicate_match_requires_review_not_rejection():
    sample = get_sample("success")
    master = [{"record_id": "DEMO-PARTIAL", "legal_name": "An unrelated name", "pan": sample["vendor"]["pan"],
               "gstin": "29ZZZZZ9999Z1Z9", "status": "active"}]
    result = list(review_vendor(sample["vendor"], docs_for("success"), master))[-1]
    assert result["decision"] == "PENDING"
    assert result["duplicate"]["kind"] == "possible"
    assert "do not reject" in next(c["message"] for c in result["checks_all"] if c["id"] == "duplicate_possible")


def test_confirmed_duplicate_matches_two_identifiers():
    result = run_sample("duplicate")
    assert result["decision"] == "REJECTED"
    assert result["duplicate"]["kind"] == "confirmed"
    assert "both match" in result["reasons"][0]


def test_duplicate_submission_after_approval_is_detected_by_master():
    success = run_sample("success")
    approved_vendor = success["vendor"]
    master = SEEDED_VENDORS + [{"record_id": "VF-APPROVED", "legal_name": approved_vendor["legal_name"],
                                "pan": approved_vendor["pan"], "gstin": approved_vendor["gstin"], "status": "active"}]
    repeated = list(review_vendor(approved_vendor, docs_for("success"), master))[-1]
    assert repeated["decision"] == "REJECTED"


def test_invalid_file_extension_and_signature_are_rejected():
    assert validate_document_file("script.exe", b"MZ") == (False, "script.exe: file type is not supported. Use PDF, PNG, JPG, DOCX, XLSX, TXT or CSV.")
    valid, message = validate_document_file("not-a-pdf.pdf", b"not really a PDF")
    assert not valid
    assert "contents do not match" in message


def test_malformed_json_is_reported_and_valid_json_is_normalized():
    try:
        parse_vendor_json("{not json}")
    except ValueError as error:
        assert "Invalid JSON" in str(error)
    else:
        raise AssertionError("Malformed JSON should be rejected.")
    parsed = parse_vendor_json('{"pan":" abcde1234f ","legal_name":"  Acme  Works "}')
    assert parsed["pan"] == "ABCDE1234F"
    assert parsed["legal_name"] == "Acme Works"
    assert parse_vendor_json('{"gst_status":"Not registered"}')["gst_status"] == "not_registered"


def test_account_reference_rejects_full_number():
    sample = get_sample("success")
    sample["vendor"]["account_last4"] = "123456789012"
    result = list(review_vendor(sample["vendor"], docs_for("success"), SEEDED_VENDORS))[-1]
    assert result["decision"] == "PENDING"
    assert any(check["id"] == "account_last4" and check["status"] == "issue" for check in result["checks_all"])


def test_non_india_country_is_out_of_scope_and_stays_pending():
    sample = get_sample("success")
    sample["vendor"]["country"] = "Singapore"
    result = list(review_vendor(sample["vendor"], docs_for("success"), SEEDED_VENDORS))[-1]
    assert result["decision"] == "PENDING"
    assert any(check["id"] == "country_scope" for check in result["checks_all"])

