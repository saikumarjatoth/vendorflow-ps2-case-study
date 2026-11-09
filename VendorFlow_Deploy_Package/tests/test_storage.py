from __future__ import annotations

import hashlib
from pathlib import Path

from vendorflow.rules import demo_document_bytes, review_vendor
from vendorflow.samples import SEEDED_VENDORS, get_sample
from vendorflow.storage import get_document, get_run, initialize, list_runs, metrics, reset_demo, save_run, vendor_master


def test_run_history_documents_and_reset_are_persisted():
    db = Path(__file__).resolve().parent / ".test-run-history.sqlite3"
    for path in (db, Path(str(db) + "-wal"), Path(str(db) + "-shm")):
        path.unlink(missing_ok=True)
    initialize(db)
    assert metrics(db)["total"] == 0
    sample = get_sample("success")
    documents = []
    for doc_type in sample["documents"]:
        filename, content = demo_document_bytes(doc_type, "success")
        documents.append({"doc_type": doc_type, "filename": filename, "mime_type": "text/plain", "content": content,
                          "sha256": hashlib.sha256(content).hexdigest(), "source": "synthetic sample placeholder", "valid": True})
    stages = list(review_vendor(sample["vendor"], documents, vendor_master(db)))
    result = dict(stages[-1], stages=stages)
    run_id = save_run(sample["vendor"], result, documents, source="sample:success", db_path=db)

    stored = get_run(run_id, db)
    assert stored is not None
    assert stored["decision"] == "APPROVED"
    assert len(stored["documents"]) == 4
    assert len(list_runs(db)) == 1
    assert metrics(db) == {"total": 1, "approved": 1, "pending": 0, "rejected": 0}
    assert any(row["record_id"] == run_id for row in vendor_master(db))
    stored_file = get_document(stored["documents"][0]["document_id"], db)
    assert stored_file is not None and stored_file["content"].startswith(b"DEMONSTRATION ONLY")

    try:
        reset_demo(db)
        assert metrics(db)["total"] == 0
        assert get_run(run_id, db) is None
        assert get_document(stored["documents"][0]["document_id"], db) is None
        assert [row["record_id"] for row in vendor_master(db)] == ["DEMO-V-001"]
    finally:
        for path in (db, Path(str(db) + "-wal"), Path(str(db) + "-shm")):
            path.unlink(missing_ok=True)

