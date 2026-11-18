
import uuid
import streamlit as st

from langgraph.types import Command

from app.graph import build_claim_graph
from app.pdf_reader import extract_text_from_pdf


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Health Insurance Claim Agent",
    page_icon="🏥",
    layout="wide"
)

st.title("🏥 Health Insurance Claim Agent")
st.subheader("Multi-Agent Claim Pre-Authorization Review")

st.info(
    "Demo only. AI recommendations are not final decisions. "
    "A human reviewer must review every claim."
)


# --------------------------------------------------
# BUILD LANGGRAPH WORKFLOW
# --------------------------------------------------

@st.cache_resource
def get_claim_graph():
    return build_claim_graph()


graph = get_claim_graph()


# --------------------------------------------------
# SESSION STATE INITIALIZATION
# --------------------------------------------------

if "claim_thread_id" not in st.session_state:
    st.session_state.claim_thread_id = None

if "claim_result" not in st.session_state:
    st.session_state.claim_result = None

if "claim_paused" not in st.session_state:
    st.session_state.claim_paused = False


# --------------------------------------------------
# DOCUMENT TEXT EXTRACTION
# --------------------------------------------------

def read_uploaded_documents(uploaded_files):
    """Read text from uploaded TXT and PDF documents."""

    all_text = []

    for uploaded_file in uploaded_files:

        file_name = uploaded_file.name.lower()

        try:

            if file_name.endswith(".txt"):

                text = uploaded_file.getvalue().decode(
                    "utf-8",
                    errors="ignore"
                )

                all_text.append(text)

            elif file_name.endswith(".pdf"):

                text = extract_text_from_pdf(uploaded_file)

                if text.strip():
                    all_text.append(text)

                else:
                    st.warning(
                        f"No readable text found in {uploaded_file.name}. "
                        "Scanned PDF OCR is not implemented yet."
                    )

            elif file_name.endswith((".png", ".jpg", ".jpeg")):

                st.warning(
                    f"Image OCR is not implemented yet: "
                    f"{uploaded_file.name}"
                )

        except Exception as error:

            st.error(
                f"Error reading {uploaded_file.name}: {error}"
            )

    return "\n\n".join(all_text)


# --------------------------------------------------
# CLAIM SUBMISSION FORM
# --------------------------------------------------

st.header("Upload Claim Documents")

with st.form("claim_submission_form"):

    uploaded_files = st.file_uploader(
        "Upload Claim Documents (PDF, Image, TXT)",
        type=["pdf", "png", "jpg", "jpeg", "txt"],
        accept_multiple_files=True
    )

    st.header("Claim Information")

    col1, col2 = st.columns(2)

    with col1:

        claim_id = st.text_input(
            "Claim ID",
            value="CLM-1001"
        )

        patient_id = st.text_input(
            "Patient ID",
            value="PAT-001"
        )

        patient_name = st.text_input(
            "Patient Name",
            value="Demo Patient"
        )

        diagnosis = st.text_input(
            "Diagnosis",
            value="Acute appendicitis"
        )

        procedure = st.text_input(
            "Procedure",
            value="Appendectomy"
        )

    with col2:

        requested_amount = st.number_input(
            "Requested Amount (INR)",
            min_value=0.0,
            value=50000.0,
            step=1000.0
        )

        admission_date = st.date_input(
            "Admission Date"
        )

        hospital_name = st.text_input(
            "Hospital Name",
            value="Example City Hospital"
        )

        policy_number = st.text_input(
            "Policy Number",
            value="POL-DEMO-2026-001"
        )

    submit_claim = st.form_submit_button(
        "Submit Claim for Review",
        use_container_width=True
    )


# --------------------------------------------------
# PROCESS CLAIM SUBMISSION
# --------------------------------------------------

if submit_claim:

    if not claim_id.strip() or not patient_id.strip():

        st.error("Please enter Claim ID and Patient ID.")

    elif not policy_number.strip():

        st.error("Please enter Policy Number.")

    elif not diagnosis.strip() or not procedure.strip():

        st.error("Please enter Diagnosis and Procedure.")

    elif not uploaded_files:

        st.error("Please upload at least one claim document.")

    else:

        uploaded_document_text = read_uploaded_documents(
            uploaded_files
        )

        if not uploaded_document_text.strip():

            st.error(
                "No readable text was extracted from the uploaded documents."
            )

        else:

            # Important:
            # Keep uploaded document text separate from form identifiers.
            # Do not insert the submitted policy number into this text.
            #
            # This allows the extraction agent to read the actual
            # policy number from the uploaded document and compare it
            # with the number entered in the form.

            claim_text = f"""
ADDITIONAL CLAIM FORM DETAILS

Patient Name: {patient_name}
Diagnosis: {diagnosis}
Procedure: {procedure}
Requested Amount: {requested_amount}
Currency: INR
Admission Date: {admission_date}
Hospital Name: {hospital_name}

UPLOADED CLAIM DOCUMENT CONTENT

{uploaded_document_text}
"""

            # Fictional policy text for prototype testing.
            policy_text = f"""
FICTIONAL EXAMPLE HEALTH INSURANCE POLICY

Coverage information:

{procedure} may be covered when medically necessary,
subject to policy conditions, exclusions and limits.

Mandatory Documents:
- Admission note
- Diagnosis summary
- Procedure details
- Discharge summary

All mandatory documents must be submitted
for claim processing.

This is fictional policy text for software testing only.
"""

            # Initial LangGraph state.
            initial_state = {

                # IDs submitted through Streamlit form.
                "claim_id": claim_id.strip(),

                "patient_id": patient_id.strip(),

                # Submitted policy number.
                "policy_number": policy_number.strip(),

                # Uploaded document text and policy text.
                "claim_document_text": claim_text,

                "policy_document_text": policy_text,

                # Initial audit and error lists.
                "audit_log": [],

                "errors": [],

                # Human review starts as incomplete.
                "human_review_required": False,

                "human_review_completed": False
            }

            # Create a unique thread for this claim.
            thread_id = str(uuid.uuid4())

            config = {
                "configurable": {
                    "thread_id": thread_id
                }
            }

            try:

                with st.spinner(
                    "AI agents are processing your claim..."
                ):

                    result = graph.invoke(
                        initial_state,
                        config=config
                    )

                st.session_state.claim_thread_id = thread_id

                st.session_state.claim_result = result

                st.session_state.claim_paused = bool(
                    result.get("__interrupt__")
                )

                st.success("Claim submitted successfully!")

                st.rerun()

            except Exception as error:

                st.error(
                    f"Claim processing failed: {error}"
                )


# --------------------------------------------------
# DISPLAY CLAIM REVIEW RESULT
# --------------------------------------------------

result = st.session_state.claim_result

if result:

    st.divider()

    st.header("📋 Claim Review Result")

    extracted_data = result.get("extracted_data", {})

    decision = result.get("decision", {})

    document_check = result.get("document_check", {})

    policy_check = result.get("policy_check", {})

    # --------------------------------------------------
    # CLAIM IDENTIFICATION
    # --------------------------------------------------

    st.subheader("Claim Identification")

    st.write(
        "**Submitted Claim ID:**",
        result.get("claim_id", "Not available")
    )

    st.write(
        "**Submitted Patient ID:**",
        result.get("patient_id", "Not available")
    )

    st.write(
        "**Submitted Policy Number:**",
        result.get("policy_number", "Not available")
    )

    # --------------------------------------------------
    # EXTRACTED CLAIM INFORMATION
    # --------------------------------------------------

    st.subheader("Extracted Claim Information")

    if extracted_data:

        st.json(extracted_data)

        document_claim_id = extracted_data.get(
            "document_claim_id",
            extracted_data.get("claim_id")
        )

        document_patient_id = extracted_data.get(
            "document_patient_id",
            extracted_data.get("patient_id")
        )

        document_policy_number = extracted_data.get(
            "policy_number"
        )

        st.write(
            "**Document Extracted Claim ID:**",
            document_claim_id or "Not found"
        )

        if document_claim_id and document_claim_id != result.get("claim_id"):

            st.warning(
                "Claim ID mismatch: the uploaded document and "
                "submitted form contain different Claim IDs."
            )

        st.write(
            "**Document Extracted Patient ID:**",
            document_patient_id or "Not found"
        )

        if (
            document_patient_id
            and document_patient_id != result.get("patient_id")
        ):

            st.warning(
                "Patient ID mismatch: the uploaded document and "
                "submitted form contain different Patient IDs."
            )

    else:

        st.warning("No extracted claim information available.")

    # --------------------------------------------------
    # POLICY NUMBER VERIFICATION
    # --------------------------------------------------

    st.subheader("🔍 Policy Number Verification")

    policy_number_status = policy_check.get(
        "policy_number_status",
        "NOT AVAILABLE"
    )

    st.write(
        "**Submitted Policy Number:**",
        policy_check.get(
            "submitted_policy_number",
            result.get("policy_number", "Not available")
        )
    )

    st.write(
        "**Extracted Policy Number:**",
        policy_check.get(
            "extracted_policy_number",
            extracted_data.get("policy_number", "Not available")
        )
    )

    st.write(
        "**Comparison Status:**",
        policy_number_status
    )

    if policy_number_status == "MATCH":

        st.success("Submitted and extracted policy numbers match.")

    elif policy_number_status == "MISMATCH":

        st.error(
            "Policy number mismatch. Human verification is required."
        )

    elif policy_number_status == "NEEDS_REVIEW":

        st.warning(
            "Policy number could not be verified. "
            "Human verification is required."
        )

    if policy_check.get("reason"):

        st.write(
            "**Policy Check Reason:**",
            policy_check.get("reason")
        )

    # --------------------------------------------------
    # AI RECOMMENDATION
    # --------------------------------------------------

    st.subheader("🤖 AI Recommendation")

    ai_status = decision.get(
        "status",
        "NOT AVAILABLE"
    )

    st.write("**Recommendation:**", ai_status)

    reasons = decision.get("reasons", [])

    if reasons:

        st.write("**Reasons:**")

        for reason in reasons:
            st.write(f"- {reason}")

    # --------------------------------------------------
    # MANDATORY DOCUMENT CHECK
    # --------------------------------------------------

    st.subheader("📄 Mandatory Document Check")

    if document_check:

        st.write(
            "**Status:**",
            document_check.get("status", "NOT AVAILABLE")
        )

        st.write(
            "**Required Documents:**",
            document_check.get("required_documents", [])
        )

        st.write(
            "**Present Documents:**",
            document_check.get("present_documents", [])
        )

        st.write(
            "**Missing Documents:**",
            document_check.get("missing_documents", [])
        )

    # --------------------------------------------------
    # HUMAN REVIEW
    # --------------------------------------------------

    if st.session_state.claim_paused:

        st.divider()

        st.header("👨‍💼 Human Review")

        st.warning(
            "The AI workflow is waiting for a human reviewer."
        )

        st.write("**AI Recommendation:**", ai_status)

        if reasons:

            st.write("**AI Reasons:**")

            for reason in reasons:
                st.write(f"- {reason}")

        missing_documents = document_check.get(
            "missing_documents",
            []
        )

        if missing_documents:

            st.write("**Missing Documents:**")

            for document in missing_documents:
                st.write(f"- {document}")

        with st.form("human_review_form"):

            reviewer_name = st.text_input(
                "Reviewer Name"
            )

            review_decision = st.selectbox(
                "Human Review Decision",
                [
                    "APPROVE",
                    "REJECT",
                    "REQUEST_MORE_INFORMATION"
                ]
            )

            reviewer_notes = st.text_area(
                "Reviewer Notes"
            )

            submit_review = st.form_submit_button(
                "Submit Human Review",
                use_container_width=True
            )

        if submit_review:

            if not reviewer_name.strip():

                st.error("Please enter reviewer name.")

            elif not reviewer_notes.strip():

                st.error("Please enter reviewer notes.")

            else:

                resume_data = {

                    "review_decision": review_decision,

                    "reviewer_name": reviewer_name.strip(),

                    "reviewer_notes": reviewer_notes.strip()
                }

                resume_config = {
                    "configurable": {
                        "thread_id": st.session_state.claim_thread_id
                    }
                }

                try:

                    with st.spinner(
                        "Saving human review..."
                    ):

                        updated_result = graph.invoke(
                            Command(resume=resume_data),
                            config=resume_config
                        )

                    st.session_state.claim_result = updated_result

                    st.session_state.claim_paused = bool(
                        updated_result.get("__interrupt__")
                    )

                    st.success(
                        "Human review has been recorded."
                    )

                    st.rerun()

                except Exception as error:

                    st.error(
                        f"Unable to submit human review: {error}"
                    )

    # --------------------------------------------------
    # FINAL HUMAN DECISION
    # --------------------------------------------------

    if result.get("human_review_completed"):

        st.divider()

        st.header("✅ Human Review Completed")

        st.write(
            "**Claim ID:**",
            result.get("claim_id", "")
        )

        st.write(
            "**Reviewer:**",
            result.get("reviewer_name", "")
        )

        st.write(
            "**Human Decision:**",
            result.get("human_review_result", "")
        )

        st.write(
            "**Final Status:**",
            result.get("final_status", "")
        )

        st.write(
            "**Reviewer Notes:**",
            result.get("human_review_notes", "")
        )

        if (
            result.get("decision", {}).get("status")
            != result.get("human_review_result")
        ):

            st.warning(
                "The human decision differs from the AI recommendation. "
                "The authorized reviewer must verify all outstanding "
                "documents and policy conditions."
            )

    # --------------------------------------------------
    # COMMUNICATION DRAFT
    # --------------------------------------------------

    communication = result.get(
        "communication_draft",
        ""
    )

    if communication:

        st.divider()

        st.header("📧 Communication Draft")

        st.text(communication)

        st.caption(
            "Prototype draft only. An authorized claims team must "
            "verify it before sending."
        )

    # --------------------------------------------------
    # AUDIT LOG
    # --------------------------------------------------

    st.divider()

    st.header("📝 Audit Log")

    audit_log = result.get("audit_log", [])

    if audit_log:

        for index, entry in enumerate(audit_log, start=1):

            if isinstance(entry, dict):

                st.write(
                    f"{index}. {entry.get('agent', 'Agent')} - "
                    f"{entry.get('status', 'Recorded')}"
                )

                st.json(entry)

            else:

                st.write(f"{index}. {entry}")

    else:

        st.info("No audit records available.")

    # --------------------------------------------------
    # WORKFLOW ERRORS
    # --------------------------------------------------

    st.divider()

    st.header("⚠️ Workflow Errors")

    errors = result.get("errors", [])

    if errors:

        for error in errors:
            st.error(error)

    else:

        st.success("No workflow execution errors reported.")
