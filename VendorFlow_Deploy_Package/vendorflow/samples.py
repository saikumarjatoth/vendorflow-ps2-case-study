"""Synthetic, demonstration-only vendor submissions and seeded master record."""

from __future__ import annotations

from copy import deepcopy


SAMPLES = {
    "success": {
        "title": "Successful Vendor",
        "expected": "APPROVED",
        "description": "Complete India-based private company; normalized bank name and identifiers align.",
        "vendor": {
            "legal_name": "Aarya Logistics Private Limited", "trading_name": "Aarya Logistics",
            "entity_type": "Private Limited Company", "country": "India",
            "registration_number": "U63030MH2020PTC123456", "contact_email": "onboarding@aarya-logistics.example",
            "contact_phone": "+91 90000 10001", "pan": "ABCDE1234F", "gst_status": "registered",
            "gstin": "27ABCDE1234F1Z5", "bank_account_holder": "Aarya Logistics Pvt Ltd",
            "account_last4": "4821", "ifsc": "HDFC0001234",
        },
        "documents": ["pan_proof", "gst_certificate", "bank_proof", "business_registration"],
    },
    "missing_docs": {
        "title": "Missing Documents", "expected": "PENDING",
        "description": "Otherwise complete submission; bank proof is absent and must be requested.",
        "vendor": {
            "legal_name": "Blue Cedar Analytics Private Limited", "trading_name": "Blue Cedar Analytics",
            "entity_type": "Private Limited Company", "country": "India",
            "registration_number": "U72900KA2021PTC234567", "contact_email": "vendor@bluecedar.example",
            "contact_phone": "+91 90000 10002", "pan": "FGHIJ5678K", "gst_status": "registered",
            "gstin": "29FGHIJ5678K1Z4", "bank_account_holder": "Blue Cedar Analytics Private Limited",
            "account_last4": "1936", "ifsc": "ICIC0000456",
        },
        "documents": ["pan_proof", "gst_certificate", "business_registration"],
    },
    "bank_mismatch": {
        "title": "Bank Details Mismatch", "expected": "PENDING",
        "description": "All applicable files and formats pass; the account holder name needs human clarification.",
        "vendor": {
            "legal_name": "Mango Systems Private Limited", "trading_name": "Mango Systems",
            "entity_type": "Private Limited Company", "country": "India",
            "registration_number": "U62010TN2022PTC345678", "contact_email": "finance@mango-systems.example",
            "contact_phone": "+91 90000 10003", "pan": "LMNOP2468Q", "gst_status": "registered",
            "gstin": "33LMNOP2468Q1Z7", "bank_account_holder": "Rohan Mehta",
            "account_last4": "7642", "ifsc": "SBIN0000789",
        },
        "documents": ["pan_proof", "gst_certificate", "bank_proof", "business_registration"],
    },
    "duplicate": {
        "title": "Duplicate Vendor", "expected": "REJECTED",
        "description": "PAN and GSTIN exactly match an active demonstration vendor-master record.",
        "vendor": {
            "legal_name": "Cedar Infra Services Private Limited", "trading_name": "Cedar Infra",
            "entity_type": "Private Limited Company", "country": "India",
            "registration_number": "U45201DL2019PTC456789", "contact_email": "accounts@cedar-infra.example",
            "contact_phone": "+91 90000 10004", "pan": "PQRSX6789K", "gst_status": "registered",
            "gstin": "07PQRSX6789K1Z2", "bank_account_holder": "Cedar Infra Services Pvt Ltd",
            "account_last4": "9087", "ifsc": "AXIS0000987",
        },
        "documents": ["pan_proof", "gst_certificate", "bank_proof", "business_registration"],
    },
}


SEEDED_VENDORS = [
    {"record_id": "DEMO-V-001", "legal_name": "Cedar Infra Services Private Limited",
     "pan": "PQRSX6789K", "gstin": "07PQRSX6789K1Z2", "status": "active",
     "source": "seeded demonstration master"},
]


def get_sample(case_id: str) -> dict:
    return deepcopy(SAMPLES[case_id])

