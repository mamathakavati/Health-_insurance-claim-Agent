
import sqlite3

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import interrupt

from app.state import ClaimState

from app.agents.document_extraction import extract_claim_data
from app.agents.pii_redaction import redact_pii
from app.agents.policy_check import check_policy
from app.agents.code_validation import validate_codes
from app.agents.fraud_detection import detect_anomalies
from app.agents.decision_agent import make_decision
from app.agents.communication_agent import create_communication


# --------------------------------------------------
# 1. SQLite Checkpoint Configuration
# --------------------------------------------------

_connection = sqlite3.connect(
    "claim_checkpoints.sqlite",
    check_same_thread=False,
)

_checkpointer = SqliteSaver(_connection)
_checkpointer.setup()


# --------------------------------------------------
# 2. Human Review Node
# --------------------------------------------------

def human_review(state: ClaimState) -> dict:
    """
    Pause the workflow and wait for human review.

    AI recommendations are not final decisions.
    Every claim requires human review.
    """

    review_response = interrupt({
        "message": "Human review is required.",
        "claim_id": state.get("claim_id", ""),
        "patient_id": state.get("patient_id", ""),
        "ai_recommendation": state.get("decision", {}),
        "missing_documents": state.get(
            "document_check", {}
        ).get("missing_documents", []),
    })

    # Read the human review response.
    selected_decision = review_response.get(
        "review_decision"
    )

    reviewer_notes = review_response.get(
        "reviewer_notes", ""
    )

    reviewer_name = review_response.get(
        "reviewer_name", "Claims Reviewer"
    )

    # Validate the reviewer's selection.
    allowed_decisions = {
        "APPROVE",
        "REJECT",
        "REQUEST_MORE_INFORMATION",
    }

    if selected_decision not in allowed_decisions:
        raise ValueError(
            f"Invalid human review decision: {selected_decision}"
        )

    # --------------------------------------------------
    # 3. Check Outstanding Verification Requirements
    # --------------------------------------------------

    document_check = state.get("document_check", {})

    missing_documents = document_check.get(
        "missing_documents", []
    )

    policy = state.get("policy_check", {})

    policy_number_status = policy.get(
        "policy_number_status"
    )

    policy_not_verified = (
        policy.get("status") != "MENTIONED_IN_POLICY"
        or policy_number_status in (
            "MISMATCH",
            "NEEDS_REVIEW",
        )
    )

    # Workflow errors must also be reviewed.
    workflow_errors = state.get("errors", [])

    unresolved_issues = (
        bool(missing_documents)
        or policy_not_verified
        or bool(workflow_errors)
    )

    # --------------------------------------------------
    # 4. Determine Final Workflow Status
    # --------------------------------------------------

    if selected_decision == "APPROVE" and unresolved_issues:

        final_status = "PENDING_VERIFICATION"

    elif selected_decision == "APPROVE":

        final_status = "APPROVED_BY_REVIEWER"

    elif selected_decision == "REJECT":

        final_status = "REJECTED_BY_REVIEWER"

    elif selected_decision == "REQUEST_MORE_INFORMATION":

        final_status = "MORE_INFORMATION_REQUIRED"

    else:

        final_status = "PENDING_VERIFICATION"

    # --------------------------------------------------
    # 5. Return Human Review Results
    # --------------------------------------------------

    return {
        "human_review_required": False,

        # Preserve the actual human decision.
        "human_review_result": selected_decision,

        "human_review_notes": reviewer_notes,

        "reviewer_name": reviewer_name,

        "human_review_completed": True,

        # Final status is separate from human decision.
        "final_status": final_status,

        "audit_log": [
            (
                f"Human reviewer {reviewer_name} submitted: "
                f"{selected_decision}."
            ),
            (
                f"Final workflow status: {final_status}."
            ),
        ],
    }


# --------------------------------------------------
# 6. Build Claim Processing Workflow
# --------------------------------------------------

def build_claim_graph():

    workflow = StateGraph(ClaimState)

    # Register agents.
    workflow.add_node(
        "document_extraction",
        extract_claim_data
    )

    workflow.add_node(
        "pii_redaction",
        redact_pii
    )

    workflow.add_node(
        "policy_check",
        check_policy
    )

    workflow.add_node(
        "code_validation",
        validate_codes
    )

    workflow.add_node(
        "fraud_detection",
        detect_anomalies
    )

    workflow.add_node(
        "decision",
        make_decision
    )

    workflow.add_node(
        "human_review",
        human_review
    )

    workflow.add_node(
        "communication",
        create_communication
    )

    # --------------------------------------------------
    # 7. Define Workflow Connections
    # --------------------------------------------------

    workflow.add_edge(
        START,
        "document_extraction"
    )

    workflow.add_edge(
        "document_extraction",
        "pii_redaction"
    )

    workflow.add_edge(
        "pii_redaction",
        "policy_check"
    )

    workflow.add_edge(
        "policy_check",
        "code_validation"
    )

    workflow.add_edge(
        "code_validation",
        "fraud_detection"
    )

    workflow.add_edge(
        "fraud_detection",
        "decision"
    )

    workflow.add_edge(
        "decision",
        "human_review"
    )

    workflow.add_edge(
        "human_review",
        "communication"
    )

    workflow.add_edge(
        "communication",
        END
    )

    # Compile graph with SQLite checkpointing.
    return workflow.compile(
        checkpointer=_checkpointer
    )
