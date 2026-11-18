
from typing import TypedDict, Optional, List, Dict, Any, Annotated
from operator import add


class ClaimState(TypedDict, total=False):

    # Claim identification submitted through the form
    claim_id: str
    patient_id: str
    policy_number: str

    # Input documents
    claim_document_text: str
    policy_document_text: str

    # Extracted and protected information
    extracted_data: Dict[str, Any]
    redacted_text: str

    # Agent results
    policy_check: Dict[str, Any]
    document_check: Dict[str, Any]
    code_validation: Dict[str, Any]
    fraud_check: Dict[str, Any]
    decision: Dict[str, Any]

    # Human review
    human_review_required: bool
    human_review_result: Optional[str]
    human_review_notes: Optional[str]
    reviewer_name: Optional[str]
    human_review_completed: bool

    # Final status
    final_status: str

    # Final communication
    communication_draft: str

    # Audit and errors
    audit_log: Annotated[List[Any], add]
    errors: List[str]
