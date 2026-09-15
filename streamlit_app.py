"""ELS Registration Assistant — Streamlit Cloud deployment."""
import json
import uuid
import os
import streamlit as st
from datetime import datetime
from pathlib import Path

from extraction import extract_from_pdf, get_demo_data
from validation import validate_all
from fridge_extraction import extract_fridge_from_pdf, get_fridge_demo_data
from fridge_validation import validate_fridge

SUBMISSIONS_DIR = Path(__file__).parent / "submissions"
SUBMISSIONS_DIR.mkdir(exist_ok=True)

st.set_page_config(page_title="ELS Registration Assistant", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""<style>
    [data-testid="stSidebar"] { display: none; }
    .stAppDeployButton { display: none; }
    .block-container { padding-top: 1rem; max-width: 1200px; }
    div[data-testid="stForm"] { border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; }
    .st-key-submit_btn button { background-color: #16a34a !important; color: white !important; }
    .st-key-submit_btn button:disabled { background-color: #94a3b8 !important; }
</style>""", unsafe_allow_html=True)

REQUIRED_TV = {"type_of_television","brand","model_numbers","diagonal_screen_size","screen_aspect_ratio","year_of_manufacture","country_of_origin","test_report_reference_no","date_of_issue","test_standard","screen_area_dm2","power_input_on_mode_w","passive_standby_power_w","lab_name","lab_country"}
REQUIRED_FRIDGE = {"type","brand","model_numbers","country_of_origin","refrigerant_type","refrigerant_charge_g","test_report_reference_no","date_of_issue","test_standard","total_volume_measured_l","total_adjusted_volume_rated_l","annual_energy_consumption_kwh","lab_name","lab_country"}

TV_FIELDS = [
    ("Television Details", [("type_of_television","Type of Television"),("brand","Brand"),("model_numbers","Model No."),("definition","Definition"),("diagonal_screen_size","Diagonal Screen Size (in)"),("screen_aspect_ratio","Screen Aspect Ratio"),("colour","Colour"),("year_of_manufacture","Year of Manufacture"),("country_of_origin","Country of Origin")]),
    ("Test Report Details", [("test_report_reference_no","Reference No."),("date_of_issue","Date of Issue"),("test_standard","Test Standard"),("screen_area_dm2","Screen Area (dm2)"),("power_input_on_mode_w","Power Input ON-Mode (W)"),("passive_standby_power_w","Passive Standby (W)"),("active_high_standby_w","Active High Standby (W)"),("active_low_standby_w","Active Low Standby (W)")]),
    ("Lab Details", [("lab_type","Lab Type"),("lab_name","Lab Name"),("lab_address","Address"),("lab_country","Country")]),
]
FRIDGE_FIELDS = [
    ("Refrigerator Details", [("type","Type"),("brand","Brand"),("model_numbers","Model No."),("colour","Colour"),("features","Features"),("country_of_origin","Country of Origin"),("refrigerant_type","Refrigerant Type"),("refrigerant_charge_g","Refrigerant Charge (g)")]),
    ("Test Report Details", [("test_report_reference_no","Reference No."),("date_of_issue","Date of Issue"),("test_standard","Test Standard"),("total_volume_measured_l","Total Volume Measured (L)"),("total_adjusted_volume_rated_l","Adjusted Volume Rated (L)"),("annual_energy_consumption_kwh","Annual Energy (kWh)")]),
    ("Lab Details", [("lab_type","Lab Type"),("lab_name","Lab Name"),("lab_address","Address"),("lab_country","Country")]),
]


def load_submissions():
    subs = []
    for fp in sorted(SUBMISSIONS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        with open(fp) as f:
            subs.append(json.load(f))
    return subs


def save_submission(extracted, validation, edited, sources, product_type):
    all_pass = validation["summary"]["failed"] == 0
    has_manual = any(v == "manual" for v in sources.values())
    auto = all_pass and not has_manual
    sid = str(uuid.uuid4())[:8]
    sub = {"id": sid, "product_type": product_type, "submitted_at": datetime.now().isoformat(),
           "brand": edited.get("brand",""), "model": edited.get("model_numbers",""),
           "report_ref": edited.get("test_report_reference_no",""),
           "status": "Approved" if auto else "Pending Review",
           "auto_approved": auto, "approved_by": "system" if auto else None,
           "approved_at": datetime.now().isoformat() if auto else None,
           "registration_fields": edited, "field_sources": sources,
           "original_extracted": extracted.get("registration_fields",{}),
           "extracted": extracted, "validation": validation}
    with open(SUBMISSIONS_DIR / f"{sid}.json", "w") as f:
        json.dump(sub, f, indent=2)
    return sid, auto


def do_action(sid, action, comments=""):
    fp = SUBMISSIONS_DIR / f"{sid}.json"
    with open(fp) as f:
        data = json.load(f)
    now = datetime.now().isoformat()
    if action == "delete":
        fp.unlink()
        return
    data.setdefault("history", []).append({"action": action, "by": "officer", "at": now, "comments": comments})
    if action == "approve":
        data.update(status="Approved", approved_by="officer", approved_at=now, officer_comments=comments)
    elif action == "reject":
        data.update(status="Rejected", rejected_by="officer", rejected_at=now, rejection_reason=comments)
    elif action == "return":
        data.update(status="Returned", returned_by="officer", returned_at=now, return_comments=comments)
    elif action == "deregister":
        data.update(status="De-registered", deregistered_by="officer", deregistered_at=now, deregister_reason=comments)
    with open(fp, "w") as f:
        json.dump(data, f, indent=2)


def resubmit(sid, edited, sources):
    fp = SUBMISSIONS_DIR / f"{sid}.json"
    with open(fp) as f:
        data = json.load(f)
    now = datetime.now().isoformat()
    data.setdefault("history", []).append({"action": "resubmit", "by": "supplier", "at": now, "comments": ""})
    data.update(status="Pending Review", registration_fields=edited, field_sources=sources, resubmitted_at=now)
    with open(fp, "w") as f:
        json.dump(data, f, indent=2)


# Session state defaults
for k, v in [("role", None), ("page", "dashboard"), ("data", None), ("amend_id", None), ("product_type", "tv")]:
    if k not in st.session_state:
        st.session_state[k] = v


# ==================== LANDING ====================
if st.session_state.role is None:
    st.markdown("## ELS Registration Assistant")
    st.caption("AI-Powered TV & Refrigerator Test Report Extraction & Validation")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Supplier")
        st.write("Upload test reports, check for issues, and submit registrations.")
        if st.button("Enter as Supplier", type="primary", use_container_width=True):
            st.session_state.role = "supplier"
            st.rerun()
    with c2:
        st.markdown("#### NEA Officer")
        st.write("Review submissions, approve/reject/return registrations.")
        if st.button("Enter as Officer", type="primary", use_container_width=True):
            st.session_state.role = "officer"
            st.rerun()

# ==================== SUPPLIER ====================
elif st.session_state.role == "supplier":
    col1, col2 = st.columns([6, 1])
    with col1:
        st.markdown("### ELS Registration — Supplier")
    with col2:
        if st.button("Switch Role", use_container_width=True):
            st.session_state.role = None
            st.session_state.page = "dashboard"
            st.rerun()

    # --- Dashboard ---
    if st.session_state.page == "dashboard":
        c1, c2 = st.columns([6, 2])
        with c2:
            if st.button("+ New Application", type="primary"):
                st.session_state.page = "upload"
                st.session_state.data = None
                st.session_state.amend_id = None
                st.rerun()

        subs = load_submissions()
        if not subs:
            st.info("No submissions yet. Click '+ New Application' to start.")
        else:
            for sub in subs:
                dt = datetime.fromisoformat(sub["submitted_at"])
                product_label = "Fridge" if sub.get("product_type") == "refrigerator" else "TV"
                status = sub.get("status", "Pending Review")
                with st.container(border=True):
                    cols = st.columns([1, 1, 2, 2, 2, 2])
                    cols[0].markdown(f"`{sub['id']}`")
                    cols[1].write(product_label)
                    cols[2].write(f"**{sub.get('brand','')}** {sub.get('model','')}")
                    cols[3].write(dt.strftime("%d/%m/%Y %H:%M"))
                    if status == "Approved":
                        cols[4].success(status)
                    elif status == "Rejected":
                        cols[4].error(status)
                    elif status == "Returned":
                        cols[4].warning(status)
                    else:
                        cols[4].info(status)
                    if status == "Returned":
                        if cols[5].button("Amend", key=f"amend_{sub['id']}"):
                            st.session_state.page = "results"
                            st.session_state.amend_id = sub["id"]
                            st.session_state.product_type = sub.get("product_type", "tv")
                            fp = SUBMISSIONS_DIR / f"{sub['id']}.json"
                            with open(fp) as f:
                                full = json.load(f)
                            st.session_state.data = {"extracted": full["extracted"], "validation": full["validation"],
                                                     "reg_fields": full.get("registration_fields", full["extracted"].get("registration_fields",{})),
                                                     "field_sources": full.get("field_sources",{}),
                                                     "return_comments": full.get("return_comments","")}
                            st.rerun()
                    if status == "Returned" and sub.get("return_comments"):
                        st.caption(f"Officer: _{sub['return_comments']}_")
                    if status == "Rejected" and sub.get("rejection_reason"):
                        st.caption(f"Reason: _{sub['rejection_reason']}_")

    # --- Upload ---
    elif st.session_state.page == "upload":
        if st.button("Back to My Submissions"):
            st.session_state.page = "dashboard"
            st.rerun()

        pt = st.selectbox("Product Type", ["tv", "refrigerator"], format_func=lambda x: "Television (TV)" if x == "tv" else "Refrigerator")
        st.session_state.product_type = pt

        uploaded = st.file_uploader("Upload Test Report PDF", type=["pdf"])
        c1, c2 = st.columns(2)
        with c1:
            if uploaded and st.button("Analyze Report", type="primary"):
                with st.spinner("Extracting and validating..."):
                    try:
                        pdf = uploaded.read()
                        ext_fn = extract_fridge_from_pdf if pt == "refrigerator" else extract_from_pdf
                        val_fn = validate_fridge if pt == "refrigerator" else validate_all
                        extracted = ext_fn(pdf)
                        validation = val_fn(extracted)
                        st.session_state.data = {"extracted": extracted, "validation": validation,
                                                 "reg_fields": extracted.get("registration_fields",{}),
                                                 "field_sources": {}, "return_comments": ""}
                        st.session_state.page = "results"
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
        with c2:
            if st.button("Try Demo"):
                demo_fn = get_fridge_demo_data if pt == "refrigerator" else get_demo_data
                val_fn = validate_fridge if pt == "refrigerator" else validate_all
                extracted = demo_fn()
                validation = val_fn(extracted)
                st.session_state.data = {"extracted": extracted, "validation": validation,
                                         "reg_fields": extracted.get("registration_fields",{}),
                                         "field_sources": {}, "return_comments": ""}
                st.session_state.page = "results"
                st.rerun()

    # --- Results ---
    elif st.session_state.page == "results" and st.session_state.data:
        if st.button("Back to My Submissions"):
            st.session_state.page = "dashboard"
            st.session_state.data = None
            st.rerun()

        data = st.session_state.data
        pt = st.session_state.product_type
        validation = data["validation"]
        reg = data["reg_fields"]
        existing_sources = data.get("field_sources", {})

        if data.get("return_comments"):
            st.warning(f"**Officer returned this submission:** {data['return_comments']}")

        left, right = st.columns(2)

        with left:
            st.markdown("#### Report Check")
            fail_count = validation["summary"]["failed"]
            if fail_count == 0:
                st.success(f"All {validation['summary']['total']} checks passed!")
            else:
                st.warning(f"**{fail_count} issues** found in test report. Fill in missing fields on the right.")
                for section in validation["sections"]:
                    issues = [c for c in section["checks"] if c["passed"] is not True]
                    if not issues:
                        continue
                    with st.expander(f"{section['name']} ({len(issues)} issues)", expanded=True):
                        for c in issues:
                            val = c.get("extracted_value")
                            if c["passed"] is False and not val:
                                st.markdown(f"**{c['name']}**: Missing. Expected: `{c.get('expected','')}`")
                            elif c["passed"] is False:
                                st.markdown(f"**{c['name']}**: Found `{val}` — {c['reason']}")
                            else:
                                st.markdown(f"**{c['name']}**: {c['reason']}")

        with right:
            st.markdown("#### ELS Registration Fields")
            fields = FRIDGE_FIELDS if pt == "refrigerator" else TV_FIELDS
            required = REQUIRED_FRIDGE if pt == "refrigerator" else REQUIRED_TV

            edited = {}
            sources = {}
            for section_name, section_fields in fields:
                st.markdown(f"**{section_name}**")
                for key, label in section_fields:
                    value = reg.get(key, "")
                    if isinstance(value, list):
                        value = ", ".join(str(v) for v in value)
                    elif value is not None:
                        value = str(value)
                    else:
                        value = ""
                    is_req = key in required
                    display = f"{label} *" if is_req else label
                    new_val = st.text_input(display, value=value, key=f"f_{key}")
                    edited[key] = new_val
                    if new_val and not value:
                        sources[key] = "manual"
                    elif value:
                        sources[key] = existing_sources.get(key, "extracted")
                    else:
                        sources[key] = "missing"
                st.divider()

            missing = sum(1 for k in required if not edited.get(k, "").strip())
            is_amend = st.session_state.amend_id is not None

            if missing > 0:
                st.button(f"Fill {missing} required fields to submit", disabled=True, use_container_width=True)
            else:
                label = "Re-submit" if is_amend else "Submit Registration"
                if st.button(label, type="primary", use_container_width=True, key="submit_btn"):
                    if is_amend:
                        resubmit(st.session_state.amend_id, edited, sources)
                        st.success(f"Re-submitted! ID: **{st.session_state.amend_id}**")
                    else:
                        sid, auto = save_submission(data["extracted"], data["validation"], edited, sources, pt)
                        if auto:
                            st.balloons()
                            st.success(f"**Auto-Approved!** ID: **{sid}**")
                        else:
                            st.success(f"Submitted for review. ID: **{sid}**")
                    st.session_state.page = "dashboard"
                    st.session_state.data = None
                    st.session_state.amend_id = None
                    import time; time.sleep(2)
                    st.rerun()

# ==================== OFFICER ====================
elif st.session_state.role == "officer":
    col1, col2 = st.columns([6, 1])
    with col1:
        st.markdown("### ELS Registration — Officer")
    with col2:
        if st.button("Switch Role", use_container_width=True):
            st.session_state.role = None
            st.session_state.page = "dashboard"
            st.rerun()

    if st.session_state.page == "dashboard":
        subs = load_submissions()
        if not subs:
            st.info("No submissions yet.")
        else:
            for sub in subs:
                dt = datetime.fromisoformat(sub["submitted_at"])
                product_label = "Fridge" if sub.get("product_type") == "refrigerator" else "TV"
                status = sub.get("status", "Pending Review")
                passed = sub["validation"]["summary"]["passed"]
                total = sub["validation"]["summary"]["total"]

                with st.container(border=True):
                    cols = st.columns([1, 1, 2, 1, 1, 1, 2])
                    cols[0].markdown(f"`{sub['id']}`")
                    cols[1].write(product_label)
                    cols[2].write(f"**{sub.get('brand','')}** {sub.get('model','')}")
                    cols[3].write(f"{passed}/{total}")
                    if status == "Approved":
                        cols[4].success(status)
                    elif status in ("Rejected", "De-registered"):
                        cols[4].error(status)
                    elif status == "Returned":
                        cols[4].warning(status)
                    else:
                        cols[4].info(status)

                    with cols[5]:
                        if st.button("View", key=f"v_{sub['id']}"):
                            st.session_state.page = f"detail_{sub['id']}"
                            st.rerun()
                    with cols[6]:
                        bc1, bc2 = st.columns(2)
                        if status == "Approved":
                            if bc1.button("De-reg", key=f"dr_{sub['id']}"):
                                st.session_state[f"action_{sub['id']}"] = "deregister"
                                st.rerun()
                        if bc2.button("Del", key=f"dl_{sub['id']}"):
                            st.session_state[f"action_{sub['id']}"] = "delete"
                            st.rerun()

                    action_key = f"action_{sub['id']}"
                    if st.session_state.get(action_key):
                        act = st.session_state[action_key]
                        if act == "delete":
                            st.warning("Confirm delete?")
                            c1, c2 = st.columns(2)
                            if c1.button("Yes, delete", key=f"yd_{sub['id']}"):
                                do_action(sub["id"], "delete")
                                del st.session_state[action_key]
                                st.rerun()
                            if c2.button("Cancel", key=f"cd_{sub['id']}"):
                                del st.session_state[action_key]
                                st.rerun()
                        elif act == "deregister":
                            reason = st.text_input("De-registration reason:", key=f"drr_{sub['id']}")
                            c1, c2 = st.columns(2)
                            if c1.button("Confirm", key=f"cdr_{sub['id']}") and reason.strip():
                                do_action(sub["id"], "deregister", reason.strip())
                                del st.session_state[action_key]
                                st.rerun()
                            if c2.button("Cancel", key=f"xdr_{sub['id']}"):
                                del st.session_state[action_key]
                                st.rerun()

    # --- Detail view ---
    elif st.session_state.page.startswith("detail_"):
        sid = st.session_state.page.replace("detail_", "")
        fp = SUBMISSIONS_DIR / f"{sid}.json"
        if not fp.exists():
            st.error("Not found")
        else:
            with open(fp) as f:
                sub = json.load(f)

            if st.button("Back to submissions"):
                st.session_state.page = "dashboard"
                st.rerun()

            pt = sub.get("product_type", "tv")
            status = sub.get("status", "Pending Review")
            mc = st.columns(5)
            mc[0].metric("ID", sub["id"])
            mc[1].metric("Product", "Fridge" if pt == "refrigerator" else "TV")
            mc[2].metric("Brand", f"{sub.get('brand','')} {sub.get('model','')}")
            mc[3].metric("Status", status)
            if sub.get("auto_approved"):
                mc[4].info("Auto-approved")

            # Actions for Pending Review
            if status == "Pending Review":
                st.divider()
                ac1, ac2, ac3 = st.columns(3)
                with ac1:
                    if st.button("Approve", type="primary", use_container_width=True):
                        do_action(sid, "approve")
                        st.rerun()
                with ac2:
                    comment = st.text_input("Return comments:", key="ret_c")
                    if st.button("Return for Clarification", use_container_width=True) and comment.strip():
                        do_action(sid, "return", comment.strip())
                        st.session_state.page = "dashboard"
                        st.rerun()
                with ac3:
                    reason = st.text_input("Rejection reason:", key="rej_r")
                    if st.button("Reject", use_container_width=True) and reason.strip():
                        do_action(sid, "reject", reason.strip())
                        st.session_state.page = "dashboard"
                        st.rerun()

            st.divider()
            left, right = st.columns(2)

            with left:
                st.markdown("#### Validation")
                summary = sub["validation"]["summary"]
                m1, m2, m3 = st.columns(3)
                m1.metric("Total", summary["total"])
                m2.metric("Passed", summary["passed"])
                m3.metric("Failed", summary["failed"])

                for section in sub["validation"]["sections"]:
                    checks = section["checks"]
                    sf = sum(1 for c in checks if c["passed"] is False)
                    label = f"{section['name']} ({len(checks)} checks" + (f", {sf} failed)" if sf else ")")
                    with st.expander(label, expanded=(sf > 0)):
                        for c in checks:
                            icon = "✅" if c["passed"] is True else "❌" if c["passed"] is False else "⚠️"
                            v = f" `{c['extracted_value']}`" if c.get("extracted_value") not in (None, "", False) else ""
                            st.markdown(f"{icon} **{c['name']}**: {c['reason']}{v}")

            with right:
                st.markdown("#### Registration Fields")
                reg = sub.get("registration_fields", sub.get("extracted", {}).get("registration_fields", {}))
                srcs = sub.get("field_sources", {})
                manual_count = sum(1 for v in srcs.values() if v == "manual")
                if manual_count:
                    st.warning(f"**{manual_count} fields manually entered** — verify against document.")

                fields = FRIDGE_FIELDS if pt == "refrigerator" else TV_FIELDS
                for section_name, section_fields in fields:
                    st.markdown(f"**{section_name}**")
                    for key, label in section_fields:
                        val = reg.get(key, "")
                        src = srcs.get(key, "extracted")
                        badge = "🟡 Manual" if src == "manual" else "🟢 Extracted" if val else "🔴 Missing"
                        st.markdown(f"<small style='color:#64748b;'>{label}</small> <small>{badge}</small><br><strong>{val or 'N/A'}</strong>", unsafe_allow_html=True)
                    st.divider()

            # History
            if sub.get("history"):
                st.markdown("#### Audit Trail")
                for h in sub["history"]:
                    icons = {"approve": "✅", "reject": "❌", "return": "↩️", "resubmit": "📤", "deregister": "🚫"}
                    st.markdown(f"{icons.get(h['action'],'•')} **{h['action'].title()}** by {h['by']} — {h['at'][:16]}" + (f"\n> {h['comments']}" if h.get("comments") else ""))
