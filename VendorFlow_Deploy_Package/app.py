from __future__ import annotations

import hashlib
from html import escape
import json
import mimetypes
import time
from datetime import datetime

import streamlit as st

from vendorflow.rules import (
    DOCUMENT_LABELS,
    FIELDS,
    FIELD_LABELS,
    demo_document_bytes,
    parse_vendor_json,
    review_vendor,
    validate_document_file,
)
from vendorflow.samples import SAMPLES, get_sample
from vendorflow.storage import (
    get_document,
    get_run,
    initialize,
    list_runs,
    metrics,
    reset_demo,
    save_run,
    vendor_master,
)


st.set_page_config(page_title="VendorFlow | Vendor onboarding", page_icon="📋", layout="wide")
initialize()

st.markdown("""
<style>
:root { --ink:#17253a; --muted:#65748a; --line:#e4e9f0; --blue:#285cb2; --blue-soft:#eef4ff; --green:#167450; --green-bg:#eaf7f1; --amber:#99620a; --amber-bg:#fff6e4; --red:#a83b3b; --red-bg:#fff0ef; --text-color:#17253a; --secondary-text-color:#475569; }
html, body, [class*="css"] { font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; color:var(--ink); }
.stApp { background:#f6f8fb; color:var(--ink)!important; }
[data-testid="stMain"], [data-testid="stSidebar"] { color:var(--ink)!important; }
.block-container { max-width:1240px; padding-top:1.7rem; padding-bottom:3rem; }
h1,h2,h3 { font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif!important; letter-spacing:-.025em; color:var(--ink)!important; }
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li { color:var(--ink)!important; }
/* Keep the existing dark alert surface; change only its text to white. */
div[data-testid="stAlert"] {
    background-color:#1d2e47!important;
    border:1px solid #1d2e47!important;
}
div[data-testid="stAlert"] p,
div[data-testid="stAlert"] span,
div[data-testid="stAlert"] [data-testid="stMarkdownContainer"],
div[data-testid="stAlert"] [data-testid="stMarkdownContainer"] * {
    color:#ffffff!important;
    -webkit-text-fill-color:#ffffff!important;
}
/* Translucent top toolbar: lets scrolled page content show through. */
header[data-testid="stHeader"],
div[data-testid="stToolbar"] {
    background-color:rgba(246,248,251,0.62)!important;
    -webkit-backdrop-filter:blur(10px);
    backdrop-filter:blur(10px);
}
header[data-testid="stHeader"] *,
div[data-testid="stToolbar"] * {
    color:#17253a!important;
    fill:#17253a!important;
}
header[data-testid="stHeader"] button,
div[data-testid="stToolbar"] button {
    color:#17253a!important;
}
h1 { font-size:2rem!important; font-weight:800!important; }
h2 { font-size:1.35rem!important; font-weight:700!important; }
h3 { font-size:1.05rem!important; font-weight:700!important; }
[data-testid="stSidebar"] { background:#fff; border-right:1px solid var(--line); }
[data-testid="stSidebar"] .block-container { padding-top:1.25rem; }
.brand { font-size:1.26rem; font-weight:800; letter-spacing:-.04em; color:#17253a; margin:.35rem 0 1.35rem; }
.brand span { color:#285cb2; }
.eyebrow { text-transform:uppercase; letter-spacing:.11em; font-size:.68rem; font-weight:700; color:#738196; }
.subtle { color:var(--muted); font-size:.91rem; }
.kpi { background:white; border:1px solid var(--line); border-radius:13px; padding:16px 18px; min-height:105px; }
.kpi-label { color:#69788d; font-size:.79rem; font-weight:600; }
.kpi-value { margin-top:8px; font-size:1.72rem; font-weight:800; color:#1d2e47; }
.panel { background:white; border:1px solid var(--line); border-radius:14px; padding:18px 20px; }
.sample-card { background:white; border:1px solid var(--line); border-radius:13px; padding:16px; height:100%; }
.run-id { font-family:ui-monospace,monospace; color:#61728b; font-size:.83rem; }
.status-pill { display:inline-block; white-space:nowrap; border-radius:99px; padding:4px 10px; font-size:.72rem; line-height:1.2; font-weight:700; letter-spacing:.025em; }
.status-approved { color:var(--green); background:var(--green-bg); }
.status-pending { color:var(--amber); background:var(--amber-bg); }
.status-rejected { color:var(--red); background:var(--red-bg); }
.status-review { color:var(--amber); background:var(--amber-bg); }
div[data-testid="stMetric"] { background:white; border:1px solid var(--line); border-radius:12px; padding:13px 16px; }
div[data-testid="stMetric"] label { color:#65748a; }
.stButton>button { color:#17253a!important; background:#fff!important; border:1px solid #cbd5e1!important; border-radius:8px; font-weight:600; }
.stButton>button[kind="primary"] { color:#fff!important; background:#285cb2!important; border-color:#285cb2!important; }
.stButton>button p { color:inherit!important; }
button[data-testid="stBaseButton-secondary"] { color:#17253a!important; background:#fff!important; border:1px solid #cbd5e1!important; }
button[data-testid="stBaseButton-secondary"] * { color:inherit!important; }
button[data-testid="stBaseButton-primary"] { color:#fff!important; background:#285cb2!important; border-color:#285cb2!important; }
button[data-testid="stBaseButton-primary"] * { color:inherit!important; }
.stProgress > div > div > div { background-color:#285cb2; }
hr { border-color:var(--line); }
/* Keep the existing dark expander bars; change only their text to white. */
[data-testid="stExpander"] details > summary,
[data-testid="stExpander"] [data-testid="stExpanderHeader"] {
    background:#1d2e47!important;
}
[data-testid="stExpander"] details > summary *,
[data-testid="stExpander"] [data-testid="stExpanderHeader"] *,
[data-testid="stExpander"] summary p,
[data-testid="stExpander"] summary span,
[data-testid="stExpander"] summary div {
    color:#ffffff!important;
    -webkit-text-fill-color:#ffffff!important;
    fill:#ffffff!important;
}
/* The email body is rendered with st.text inside this expander.
   Give that text a readable ink color without changing the white panel. */
[data-testid="stExpander"] [data-testid="stText"],
[data-testid="stExpander"] [data-testid="stText"] * {
    color:#17253a!important;
    -webkit-text-fill-color:#17253a!important;
    opacity:1!important;
}
</style>
""", unsafe_allow_html=True)


def _apply_pending_state() -> None:
    if st.session_state.pop("pending_clear_uploads", False):
        for category in DOCUMENT_LABELS:
            st.session_state.pop(f"upload_{category}", None)
    pending = st.session_state.pop("pending_form_load", None)
    if pending is not None:
        for field in FIELDS:
            st.session_state[f"field_{field}"] = pending.get(field, "")
        st.session_state.loaded_sample = st.session_state.pop("pending_sample_id", None)
        st.session_state.nav = "New Submission"
    if st.session_state.pop("pending_clear_form", False):
        for field in FIELDS:
            st.session_state[f"field_{field}"] = ""
        st.session_state.loaded_sample = None
        for category in DOCUMENT_LABELS:
            st.session_state.pop(f"upload_{category}", None)
        st.session_state.nav = "New Submission"


_apply_pending_state()
# Apply navigation changes only before the radio widget is created on this rerun.
if st.session_state.pop("pending_reset_ui", False):
    st.session_state["nav"] = "Dashboard"
st.session_state.setdefault("loaded_sample", None)
st.session_state.setdefault("selected_run_id", None)
st.session_state.setdefault("selected_sample_id", "success")


def badge(decision: str) -> str:
    cls = {"APPROVED": "status-approved", "PENDING": "status-pending", "REJECTED": "status-rejected"}.get(decision, "status-review")
    return f'<span class="status-pill {cls}">{decision}</span>'


def show_checks(checks: list[dict]) -> None:
    if not checks:
        return
    for check in checks:
        icon = "✓" if check["status"] == "pass" else "!" if check["status"] in {"issue", "review"} else "•"
        tint = "#167450" if check["status"] == "pass" else "#99620a" if check["status"] == "review" else "#a83b3b"
        label = escape(str(check["label"]))
        message = escape(str(check["message"]))
        st.markdown(f"<div style='padding:6px 0;border-bottom:1px solid #f0f2f6'><b style='color:{tint};margin-right:8px'>{icon}</b><b>{label}</b><br><span class='subtle' style='margin-left:22px'>{message}</span></div>", unsafe_allow_html=True)


def render_run_detail(run: dict) -> None:
    legal_name = escape(str(run["vendor"].get("legal_name") or "(missing legal name)"))
    run_id = escape(str(run.get("run_id", "")))
    submitted_at = escape(str(run.get("submitted_at", "")))
    source = escape(str(run.get("source", "")))
    st.markdown(f"### {legal_name} &nbsp; {badge(run['decision'])}", unsafe_allow_html=True)
    st.markdown(f"<span class='run-id'>{run_id} · {submitted_at} · {source}</span>", unsafe_allow_html=True)
    st.markdown("#### Decision and next action")
    for reason in run.get("reasons", []):
        st.write(f"• {reason}")
    st.info(run.get("next_action", ""))
    with st.expander("Validation results", expanded=False):
        show_checks(run.get("checks_all", []))
    with st.expander("Processing stages", expanded=False):
        for stage in run.get("stages", []):
            st.markdown(f"**{stage['number']}. {stage['title']}** — {stage['message']}")
            if stage.get("checks"):
                show_checks(stage["checks"])
    communication = run.get("communication", {})
    with st.expander("Vendor communication draft", expanded=True):
        st.caption(communication.get("delivery", "Draft only."))
        st.markdown(f"**Subject:** {communication.get('subject','')}")
        st.text(communication.get("body", ""))
    docs = run.get("documents", [])
    if docs:
        st.markdown("#### Supporting files")
        for doc in docs:
            label = f"{DOCUMENT_LABELS.get(doc['doc_type'], doc['doc_type'])} · {doc['filename']} ({doc['size_bytes']:,} bytes)"
            content = get_document(doc["document_id"])
            if content:
                st.download_button(f"Download {doc['filename']}", content["content"], file_name=content["filename"],
                                   mime=content["mime_type"] or "application/octet-stream", key=f"download_{doc['document_id']}")
            else:
                st.caption(label)


def load_sample(case_id: str) -> None:
    st.session_state.pending_form_load = get_sample(case_id)["vendor"]
    st.session_state.pending_sample_id = case_id
    st.session_state.pending_clear_uploads = True


with st.sidebar:
    st.markdown("<div class='brand'>Vendor<span>Flow</span></div>", unsafe_allow_html=True)
    st.markdown("<div class='eyebrow'>Vendor operations</div>", unsafe_allow_html=True)
    nav = st.radio("Workspace", ["Dashboard", "New Submission", "Run History", "Rules & Demo"], key="nav", label_visibility="collapsed")
    st.divider()
    st.caption("Local demo workspace")
    st.caption("Synthetic sample records · no external verification")
    if st.button("Reset demo dataset", use_container_width=True, help="Clears all run history and uploaded files, then restores the seeded sample vendor."):
        st.session_state.show_reset_confirm = True
    if st.session_state.pop("reset_notice", False):
        st.success("Demo data restored. Previous submissions and page results have been cleared.")
    if st.session_state.get("show_reset_confirm"):
        st.warning("This clears the local run history and uploaded files. The seeded demo vendor will be restored.")
        confirm_col, cancel_col = st.columns(2)
        if confirm_col.button("Confirm reset", type="primary", key="confirm_reset"):
            reset_demo()
            st.session_state.show_reset_confirm = False
            st.session_state.selected_run_id = None

            # Clear page-level results and stale widget/form state as well as the database.
            for key in (
                "last_run_for_page",
                "history_run_selector",
                "loaded_sample",
                "pending_form_load",
                "pending_sample_id",
                "pending_clear_uploads",
                "pending_clear_form",
                "json_input",
            ):
                st.session_state.pop(key, None)
            for field in FIELDS:
                st.session_state.pop(f"field_{field}", None)
            for category in DOCUMENT_LABELS:
                st.session_state.pop(f"upload_{category}", None)

            # The nav radio has already been instantiated in this run, so defer its
            # reset until the next run, before that widget is created.
            st.session_state["pending_reset_ui"] = True
            st.session_state["reset_notice"] = True
            st.rerun()
        if cancel_col.button("Cancel", key="cancel_reset"):
            st.session_state.show_reset_confirm = False
            st.rerun()


st.markdown("<div class='eyebrow'>Operations · India vendor onboarding</div>", unsafe_allow_html=True)


if nav == "Dashboard":
    st.title("Vendor onboarding dashboard")
    st.markdown("Track each submission from intake through an explainable decision.")
    m = metrics()
    kpis = [("Total submissions", m["total"]), ("Approved", m["approved"]), ("Pending review", m["pending"]), ("Rejected duplicates", m["rejected"])]
    cols = st.columns(4)
    for col, (label, value) in zip(cols, kpis):
        col.markdown(f"<div class='kpi'><div class='kpi-label'>{label}</div><div class='kpi-value'>{value}</div></div>", unsafe_allow_html=True)

    st.markdown("## Try a Sample Submission")
    st.markdown("Four synthetic scenarios run through the same checks and decision logic as a manually entered submission.", unsafe_allow_html=True)
    case_cols = st.columns(2)
    for i, (case_id, sample) in enumerate(SAMPLES.items()):
        with case_cols[i % 2]:
            with st.container(border=True):
                st.markdown(f"### {sample['title']}")
                st.markdown(f"<div style='margin:2px 0 8px'><span class='subtle'>Expected</span> &nbsp; {badge(sample['expected'])}</div>", unsafe_allow_html=True)
                st.caption(sample["description"])
                with st.expander("Review details", expanded=False):
                    st.json(sample["vendor"], expanded=False)
                    attached = ", ".join(DOCUMENT_LABELS[d] for d in sample["documents"]) or "None"
                    st.caption(f"Demo attachments: {attached}")
                if st.button("Load Sample", key=f"load_{case_id}", type="primary", use_container_width=True):
                    load_sample(case_id)
                    st.rerun()
    st.markdown("## Recent activity")
    recent = list_runs(limit=5)
    if recent:
        for row in recent:
            c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
            c1.markdown(f"**{escape(str(row['legal_name']))}**<br><span class='run-id'>{escape(str(row['run_id']))}</span>", unsafe_allow_html=True)
            c2.caption(row["submitted_at"])
            c3.markdown(badge(row["decision"]), unsafe_allow_html=True)
            if c4.button("Open", key=f"open_recent_{row['run_id']}"):
                st.session_state.selected_run_id = row["run_id"]
                st.session_state.nav = "Run History"
                st.rerun()
    else:
        st.info("No submissions yet. Load the successful sample to see the process run end to end.")
    st.caption("Documents in this demo are labeled placeholders. Uploaded files are stored in the local SQLite database. No email is sent.")


elif nav == "New Submission":
    st.title("New vendor submission")
    st.markdown("Enter the vendor's self-reported details and attach supporting files. The workflow checks formats and availability, then routes unresolved cases for review.")
    loaded = st.session_state.get("loaded_sample")
    if loaded:
        sample = SAMPLES[loaded]
        st.info(f"Loaded sample: **{sample['title']}** · expected demonstration outcome: **{sample['expected']}**. Edit any fields before running.")
        if st.button("Clear sample and start blank"):
            st.session_state.pending_clear_form = True
            st.rerun()

    with st.expander("Optional: load vendor details from JSON", expanded=False):
        st.caption("Paste a JSON object using the form field keys. Files are attached below, not embedded in JSON.")
        json_example = {"legal_name": "", "trading_name": "", "entity_type": "Private Limited Company", "country": "India",
                        "registration_number": "", "contact_email": "", "contact_phone": "", "pan": "", "gst_status": "registered",
                        "gstin": "", "bank_account_holder": "", "account_last4": "", "ifsc": ""}
        raw_json = st.text_area("Vendor JSON", value=json.dumps(json_example, indent=2), height=180, key="json_input")
        if st.button("Load JSON into form", key="load_json"):
            try:
                st.session_state.pending_form_load = parse_vendor_json(raw_json)
                st.session_state.pending_sample_id = None
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

    with st.form("vendor_form", clear_on_submit=False):
        st.markdown("### Company details")
        a, b = st.columns(2)
        with a:
            legal_name = st.text_input("Legal business name *", key="field_legal_name")
            trading_name = st.text_input("Trading name", key="field_trading_name")
            entity_type = st.selectbox("Entity type *", ["Private Limited Company", "Public Limited Company", "LLP", "Partnership", "Sole Proprietorship"], key="field_entity_type")
            country = st.selectbox("Country *", ["India"], key="field_country", help="This demonstration applies India-specific PAN, GSTIN and IFSC checks.")
        with b:
            registration_number = st.text_input("Business registration number", key="field_registration_number", help="Required for companies, LLPs and partnerships in this demo.")
            contact_email = st.text_input("Contact email *", key="field_contact_email")
            contact_phone = st.text_input("Contact number *", key="field_contact_phone")
        st.markdown("### Tax details")
        a, b, c = st.columns(3)
        with a:
            pan = st.text_input("PAN *", key="field_pan", max_chars=10)
        with b:
            gst_status = st.selectbox("GST registration status *", ["registered", "not_registered"], key="field_gst_status")
        with c:
            gstin = st.text_input("GSTIN", key="field_gstin", max_chars=15, disabled=gst_status != "registered")
        st.markdown("### Banking details")
        a, b, c = st.columns(3)
        with a:
            bank_account_holder = st.text_input("Bank account holder name *", key="field_bank_account_holder")
        with b:
            account_last4 = st.text_input("Account last four digits *", key="field_account_last4", max_chars=4)
        with c:
            ifsc = st.text_input("IFSC *", key="field_ifsc", max_chars=11)
        st.caption("For demo privacy, this form accepts only the account's last four digits, not a full account number.")
        st.markdown("### Supporting documents")
        st.caption("Accepted: PDF, PNG, JPG, DOCX, XLSX, TXT and CSV; maximum 10 MB each. Upload availability is checked, not authenticity.")
        upload_values = {}
        file_types = ["pdf", "png", "jpg", "jpeg", "docx", "xlsx", "txt", "csv"]
        for category in ("pan_proof", "gst_certificate", "bank_proof", "business_registration", "other"):
            upload_values[category] = st.file_uploader(DOCUMENT_LABELS[category], type=file_types, accept_multiple_files=True, key=f"upload_{category}")
        if loaded:
            sample_docs = SAMPLES[loaded]["documents"]
            labels = ", ".join(DOCUMENT_LABELS[d] for d in sample_docs) if sample_docs else "No files preloaded"
            st.caption(f"Sample placeholder files attached: {labels}")
        submitted = st.form_submit_button("Submit and run review", type="primary", use_container_width=True)

    if submitted:
        vendor = {"legal_name": legal_name, "trading_name": trading_name, "entity_type": entity_type,
                  "country": country, "registration_number": registration_number, "contact_email": contact_email,
                  "contact_phone": contact_phone, "pan": pan, "gst_status": gst_status, "gstin": gstin,
                  "bank_account_holder": bank_account_holder, "account_last4": account_last4, "ifsc": ifsc}
        documents = []
        if loaded:
            for doc_type in SAMPLES[loaded]["documents"]:
                filename, content = demo_document_bytes(doc_type, loaded)
                documents.append({"doc_type": doc_type, "filename": filename, "mime_type": "text/plain", "content": content,
                                  "sha256": hashlib.sha256(content).hexdigest(), "source": "synthetic sample placeholder", "valid": True})
        for doc_type, file_list in upload_values.items():
            for uploaded in file_list or []:
                content = uploaded.getvalue()
                valid, message = validate_document_file(uploaded.name, content)
                documents.append({"doc_type": doc_type, "filename": uploaded.name,
                                  "mime_type": uploaded.type or mimetypes.guess_type(uploaded.name)[0] or "application/octet-stream",
                                  "content": content, "sha256": hashlib.sha256(content).hexdigest(),
                                  "source": "user upload", "valid": valid, "error": message if not valid else None})
        stages = []
        final = None
        st.markdown("## Live processing")
        progress = st.progress(0, text="Starting the review")
        for stage in review_vendor(vendor, documents, vendor_master()):
            status = st.status(f"Stage {stage['number']} · {stage['title']}", state="running", expanded=True)
            status.write(stage["message"])
            show_checks(stage.get("checks", []))
            stages.append(stage)
            status.update(label=f"Stage {stage['number']} · {stage['title']}", state="complete")
            progress.progress(stage["number"] / 8, text=f"Completed {stage['number']} of 8 stages")
            if stage["number"] < 8:
                time.sleep(0.22)
            if stage.get("communication"):
                final = dict(stage)
        if final:
            final["stages"] = stages
            case_id = st.session_state.get("loaded_sample")
            source = f"sample:{case_id}" if case_id else "manual"
            run_id = save_run(vendor, final, documents, source=source)
            final["run_id"] = run_id
            saved = get_run(run_id)
            st.session_state.last_run_for_page = saved
            st.session_state.loaded_sample = None
            st.session_state.pending_clear_uploads = True
            st.success("Processing completed and the result was saved to Run History.")

    if st.session_state.get("last_run_for_page"):
        st.markdown("## Decision summary")
        render_run_detail(st.session_state.last_run_for_page)


elif nav == "Run History":
    st.title("Run history")
    rows = list_runs()
    if not rows:
        st.info("No runs yet. Go to the dashboard and load a sample submission, or enter a vendor manually.")
    else:
        summary = [{"Run ID": row["run_id"], "Submitted (UTC)": row["submitted_at"], "Vendor": row["legal_name"],
                    "Decision": row["decision"], "Source": row["source"]} for row in rows]
        st.dataframe(summary, use_container_width=True, hide_index=True)
        options = [row["run_id"] for row in rows]
        default_index = options.index(st.session_state.selected_run_id) if st.session_state.selected_run_id in options else 0
        chosen = st.selectbox("Inspect a submission", options, index=default_index, key="history_run_selector",
                              format_func=lambda rid: f"{rid} · {next((r['legal_name'] for r in rows if r['run_id'] == rid), '')}")
        run = get_run(chosen)
        if run:
            st.divider()
            render_run_detail(run)


else:
    st.title("Rules, assumptions & demo guide")
    st.markdown("A deterministic first-pass review helps operations staff focus on the cases that need judgment.")
    st.markdown("### Processing stages")
    for num, title, detail in [
        (1, "Submission received", "Record intake time and attached file count."),
        (2, "Information normalisation", "Collapse whitespace; uppercase PAN, GSTIN and IFSC."),
        (3, "Field validation", "Check required fields, PAN/GSTIN structure and relationship, email, phone, IFSC and last-four-only bank reference."),
        (4, "Document completeness", "Compare tagged attachments with entity and GST applicability; inspect file extension, size and basic signature."),
        (5, "Cross-field consistency", "Compare legal entity and bank-holder name; partial or absent overlap routes to human review."),
        (6, "Duplicate detection", "Compare active demo master on exact PAN + GSTIN; a one-field or name-only match is only a possible duplicate."),
        (7, "Decision generation", "Approve a complete, consistent record; keep issues pending; reject only an exact PAN + GSTIN match."),
        (8, "Communication preparation", "Prepare an approved, pending or duplicate notice for a human to send."),
    ]:
        st.markdown(f"**{num}. {title}**  \n{detail}")
    st.markdown("### Business rules and boundaries")
    st.markdown("""
- Private and public companies, LLPs and partnerships require a business registration number and document. Proprietorships do not in this demo.
- PAN proof and bank proof are always required. A GST certificate is required only when GST status is Registered.
- Identifier checks verify expected string structure and the PAN embedded in GSTIN. They do not query government systems.
- Document checks confirm attachment availability, file type, size and basic signature only. They do not read document content or establish authenticity.
- A bank-holder name difference is a review flag, not a fraud finding. Shared words are treated as uncertain and still require a person to confirm.
- A confirmed duplicate requires both PAN and GSTIN to match one active record. A partial identifier or name-only match is PENDING.
- A newly approved submission enters the local active master, so rerunning the same approved vendor is treated as a duplicate. Reset restores the one seeded sample vendor and clears run history/files.
- Bank account collection is masked to last four digits. Uploaded files are stored in the local SQLite database for the local demo. No email is sent.
""")
    st.markdown("### Public deployment note")
    st.markdown("`render.yaml` is included for an optional Render deployment. The starter uses SQLite on the service filesystem; free hosted filesystems can reset, so run history there is demo-only unless a persistent disk or managed database is configured.")
    st.caption("All supplied vendor values and document placeholders are synthetic and for demonstration only.")

