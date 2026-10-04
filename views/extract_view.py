"""Document Extraction view: Image/PDF upload, Camera input, Gemini extraction, and Review Screen."""
import streamlit as st
import os
from typing import List, Dict, Any
from datetime import date
from services.gemini_service import GeminiService
from services.deadline_service import DeadlineService
from models.deadline import DeadlineType
from utils.date_utils import format_display_date


def render_extract_page(deadline_service: DeadlineService, gemini_service: GeminiService):
    st.markdown(
        """
        <div style="margin-bottom: 24px;">
            <h1 style="margin: 0; font-size: 2.2rem; font-weight: 700; color: #f8fafc;">Extract Deadlines</h1>
            <p style="margin: 4px 0 0 0; color: #94a3b8; font-size: 1.05rem;">
                Upload an academic document and let AI find the important dates.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Initialize review state if not set
    if "extracted_items" not in st.session_state:
        st.session_state.extracted_items = []
    if "source_doc_name" not in st.session_state:
        st.session_state.source_doc_name = "document"

    # Tab selection for input methods
    tab_upload, tab_camera, tab_sample = st.tabs(["📁 File Upload", "📷 Camera Capture", "📋 Sample Document"])

    file_bytes = None
    mime_type = None
    filename = "academic_document"

    with tab_upload:
        uploaded_file = st.file_uploader(
            "Choose a syllabus, timetable, or assignment document",
            type=["png", "jpg", "jpeg", "pdf"],
            help="Supported formats: PNG, JPG, JPEG, PDF"
        )
        if uploaded_file is not None:
            file_bytes = uploaded_file.getvalue()
            filename = uploaded_file.name
            mime_type = uploaded_file.type or ("application/pdf" if filename.lower().endswith(".pdf") else "image/png")
            
            if "pdf" in mime_type:
                st.info(f"📄 PDF loaded: **{filename}** ({len(file_bytes) / 1024:.1f} KB)")
            else:
                st.image(file_bytes, caption=f"Uploaded: {filename}", use_container_width=True)

    with tab_camera:
        camera_img = st.camera_input("Photograph your timetable, syllabus, or notice board")
        if camera_img is not None:
            file_bytes = camera_img.getvalue()
            filename = "camera_capture.png"
            mime_type = "image/png"

    with tab_sample:
        st.markdown("Test extraction with a realistic pre-generated academic schedule containing assignments, quizzes, and exams.")
        sample_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "samples", "sample_academic_schedule.png")
        if os.path.exists(sample_path):
            st.image(sample_path, caption="Sample Academic Schedule (CS Dept)", use_container_width=True)
            if st.button("Use Sample Document for Extraction", key="btn_use_sample"):
                with open(sample_path, "rb") as f:
                    file_bytes = f.read()
                filename = "sample_academic_schedule.png"
                mime_type = "image/png"
                st.session_state["trigger_sample_extract"] = True
        else:
            st.warning("Sample image not found on disk.")

    # Trigger extraction if sample was chosen
    if st.session_state.get("trigger_sample_extract"):
        st.session_state["trigger_sample_extract"] = False
        with open(sample_path, "rb") as f:
            file_bytes = f.read()
        filename = "sample_academic_schedule.png"
        mime_type = "image/png"

    # Action Button
    st.write("")
    extract_col1, extract_col2 = st.columns([2, 5])
    with extract_col1:
        start_extract = st.button("🔍 Extract Deadlines", type="primary", use_container_width=True, disabled=file_bytes is None)

    if start_extract and file_bytes:
        with st.spinner("Analyzing your document with Gemini multimodal AI..."):
            success, err_msg, items = gemini_service.extract_deadlines(
                file_bytes=file_bytes,
                mime_type=mime_type,
                filename=filename
            )

        if not success:
            st.error(f"❌ {err_msg}")
        elif not items:
            st.warning(err_msg or "No clear academic deadlines were found in the uploaded document.")
        else:
            st.session_state.extracted_items = []
            for idx, itm in enumerate(items):
                itm["_selected"] = True
                itm["_index"] = idx
                st.session_state.extracted_items.append(itm)
            st.session_state.source_doc_name = filename
            st.success(f"✨ Successfully extracted **{len(items)}** deadlines! Please review and confirm below.")
            st.rerun()

    # SECTION 13: EXTRACTION REVIEW SCREEN
    if st.session_state.extracted_items:
        st.divider()
        st.markdown("### 📋 Review Extracted Deadlines")
        st.caption("AI results require human verification. Verify each date, subject, and title before saving to your persistent tracker.")

        # Check for duplicates across current extraction
        duplicate_warnings = {}
        for itm in st.session_state.extracted_items:
            dups = deadline_service.find_possible_duplicates(
                title=itm.get("title", ""),
                subject=itm.get("subject", ""),
                deadline_date=itm.get("deadline_date", "")
            )
            if dups:
                duplicate_warnings[itm["_index"]] = dups

        if duplicate_warnings:
            st.warning(f"⚠️ **Duplicate Alert**: {len(duplicate_warnings)} item(s) may already exist in your database.")

        # Header controls
        col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([2, 2, 3])
        with col_ctrl1:
            if st.button("Select All"):
                for itm in st.session_state.extracted_items:
                    itm["_selected"] = True
                st.rerun()
        with col_ctrl2:
            if st.button("Deselect All"):
                for itm in st.session_state.extracted_items:
                    itm["_selected"] = False
                st.rerun()
        with col_ctrl3:
            with st.popover("➕ Add Extra Deadline to List"):
                new_t = st.text_input("Title", key="rev_new_t")
                new_s = st.text_input("Subject", key="rev_new_s", value="General")
                new_tp = st.selectbox("Type", [t.value for t in DeadlineType], key="rev_new_tp")
                new_d = st.date_input("Date", value=date.today(), key="rev_new_d")
                new_tm = st.text_input("Time (optional)", key="rev_new_tm")
                new_desc = st.text_area("Description", key="rev_new_desc")
                if st.button("Add to Review", key="rev_add_btn"):
                    if new_t:
                        new_idx = len(st.session_state.extracted_items)
                        st.session_state.extracted_items.append({
                            "_selected": True,
                            "_index": new_idx,
                            "title": new_t,
                            "subject": new_s,
                            "type": new_tp,
                            "deadline_date": new_d.strftime("%Y-%m-%d"),
                            "deadline_time": new_tm if new_tm.strip() else None,
                            "description": new_desc,
                            "confidence": "high",
                            "source_document": "manual_entry",
                            "source_text": "Added during extraction review",
                        })
                        st.toast("Item added to review list", icon="➕")
                        st.rerun()
                    else:
                        st.error("Title is required.")

        st.write("")

        # Render each extracted deadline item
        indices_to_delete = []

        for idx, itm in enumerate(st.session_state.extracted_items):
            itm_index = itm["_index"]
            conf = itm.get("confidence", "high").lower()
            conf_badge = {
                "high": "🟢 High Confidence",
                "medium": "🟡 Medium Confidence - Please verify date",
                "low": "🔴 Low Confidence - Review carefully"
            }.get(conf, "🟡 Medium")

            has_dup = itm_index in duplicate_warnings

            with st.container():
                st.markdown(
                    f"""
                    <div style="background-color: #1e293b; border-left: 4px solid {'#eab308' if conf == 'medium' else ('#ef4444' if conf == 'low' else '#3b82f6')}; border-radius: 8px; padding: 14px; margin-bottom: 12px; border: 1px solid rgba(255,255,255,0.06);">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <span style="font-size: 0.8rem; font-weight: 600; color: #94a3b8;">Item #{idx + 1}</span>
                            <span style="font-size: 0.75rem; color: {'#facc15' if conf == 'medium' else ('#f87171' if conf == 'low' else '#4ade80')}; font-weight: 600;">
                                {conf_badge}
                            </span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                if has_dup:
                    dup_records = duplicate_warnings[itm_index]
                    st.warning(
                        f"⚠️ **Possible duplicate found:** '{dup_records[0].title}' in '{dup_records[0].subject}' is already recorded for {dup_records[0].deadline_date}."
                    )

                c_sel, c_t, c_s, c_type, c_date, c_del = st.columns([0.8, 3, 2, 2, 2, 0.8])
                with c_sel:
                    itm["_selected"] = st.checkbox(
                        "Keep",
                        value=itm.get("_selected", True),
                        key=f"sel_{itm_index}",
                        label_visibility="collapsed"
                    )
                with c_t:
                    itm["title"] = st.text_input("Title", value=itm.get("title", ""), key=f"title_{itm_index}", label_visibility="collapsed")
                with c_s:
                    itm["subject"] = st.text_input("Subject", value=itm.get("subject", ""), key=f"subj_{itm_index}", label_visibility="collapsed")
                with c_type:
                    all_types = [t.value for t in DeadlineType]
                    cur_t = itm.get("type", "Assignment")
                    t_idx = all_types.index(cur_t) if cur_t in all_types else 0
                    itm["type"] = st.selectbox("Type", all_types, index=t_idx, key=f"type_{itm_index}", label_visibility="collapsed")
                with c_date:
                    itm["deadline_date"] = st.text_input("Date (YYYY-MM-DD)", value=itm.get("deadline_date", ""), key=f"date_{itm_index}", label_visibility="collapsed")
                with c_del:
                    if st.button("❌", key=f"del_rev_{itm_index}", help="Remove from review list"):
                        indices_to_delete.append(idx)

                # Source text snippet if present
                if itm.get("source_text"):
                    st.caption(f"📄 *Detected from text:* \"{itm['source_text']}\"")

                st.write("")

        # Delete any items marked for deletion
        if indices_to_delete:
            for d_idx in sorted(indices_to_delete, reverse=True):
                del st.session_state.extracted_items[d_idx]
            st.rerun()

        # Save Action Bar
        st.divider()
        c_save1, c_save2, c_save3 = st.columns([3, 2, 4])
        with c_save1:
            if st.button("💾 Save Selected Deadlines", type="primary", use_container_width=True):
                saved_count = 0
                selected_items = [itm for itm in st.session_state.extracted_items if itm.get("_selected", True)]

                if not selected_items:
                    st.warning("Please select at least one deadline to save.")
                else:
                    for itm in selected_items:
                        success, err, _ = deadline_service.create_deadline({
                            "title": itm.get("title"),
                            "subject": itm.get("subject"),
                            "type": itm.get("type"),
                            "deadline_date": itm.get("deadline_date"),
                            "deadline_time": itm.get("deadline_time"),
                            "description": itm.get("description", ""),
                            "confidence": itm.get("confidence", "high"),
                            "source_document": st.session_state.source_doc_name,
                            "source_text": itm.get("source_text", ""),
                        })
                        if success:
                            saved_count += 1

                    st.session_state.extracted_items = []
                    st.success(f"🎉 Successfully saved **{saved_count}** deadlines to your persistent tracker!")
                    st.toast(f"Saved {saved_count} deadlines!", icon="💾")
                    st.balloons()
                    st.rerun()

        with c_save2:
            if st.button("Clear Review List", use_container_width=True):
                st.session_state.extracted_items = []
                st.rerun()
