"""
Traceability compliance tests (reviewer checklist D, Route A).

Confirms that the PRODUCTION enforcement in
DiagramGenerationService._check_compliance and the RQ3 experiment's
enforce_case (scripts/04_rq3_traceability_experiment.py) accept and reject
the SAME elements — both are driven by the shared predicates in
backend/services/diagram/traceability_enforcement.py, and this test guards
that equivalence.

Run: python3 backend/tests/unit/test_traceability_compliance.py
"""
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.services.diagram.traceability_enforcement import (
    enforce_case,
    grounded_actor,
    grounded_message,
)
from backend.services.diagram.diagram_generator import DiagramGenerationService


REQ_TEXT = {
    "R1": "The system shall allow the customer to upload a document.",
    "R2": "The system shall store the document in the database.",
}


def _enriched_requirements():
    """Minimal enriched-requirement dicts as _check_compliance receives them."""
    return [
        {"req_id": rid, "current_text": txt, "actors_json": '["Customer", "System"]'}
        for rid, txt in REQ_TEXT.items()
    ]


CASE = {
    "req_text": REQ_TEXT,
    "actors": ["Customer", "System", "Database", "Auditor"],
    "messages": [
        {"from": "Customer", "to": "System", "text": "upload document", "req_id": "R1"},
        {"from": "System", "to": "Database", "text": "store document", "req_id": "R2"},
        # Hallucinated: cites R2 but text has zero overlap with R2.
        {"from": "System", "to": "Auditor", "text": "send audit email", "req_id": "R2"},
        # Hallucinated: cites a requirement id that does not exist.
        {"from": "System", "to": "Customer", "text": "notify user", "req_id": "R99"},
    ],
}


class TestSharedPredicates(unittest.TestCase):
    def test_grounded_actor_accepts_named_actor(self):
        self.assertTrue(grounded_actor("Customer", REQ_TEXT))

    def test_grounded_actor_rejects_invented_actor(self):
        self.assertFalse(grounded_actor("Auditor", REQ_TEXT))

    def test_grounded_message_accepts_overlap(self):
        self.assertTrue(grounded_message("upload document", "R1", REQ_TEXT))

    def test_grounded_message_rejects_no_overlap(self):
        self.assertFalse(grounded_message("send audit email", "R2", REQ_TEXT))

    def test_grounded_message_rejects_unknown_req(self):
        self.assertFalse(grounded_message("notify user", "R99", REQ_TEXT))



class TestProductionMatchesExperiment(unittest.TestCase):
    """_check_compliance (usecase + sequence) must keep/reject the same
    elements as the RQ3 experiment's enforce_case."""

    def test_enforce_case_rejections(self):
        out = enforce_case(CASE)
        # Auditor is not grounded in any requirement text; the other three are.
        self.assertEqual(set(out["actors"]), {"Customer", "System", "Database"})
        # Only the two lexically grounded, traceable messages survive.
        kept_texts = {(m["from"], m["text"]) for m in out["messages"]}
        self.assertEqual(
            kept_texts, {("Customer", "upload document"), ("System", "store document")}
        )
        # Rejection counts: 1 actor, 2 messages.
        self.assertEqual(out["rejected"], (1, 2))

    def test_production_sequence_matches_experiment(self):
        svc = object.__new__(DiagramGenerationService)  # no DB/LLM needed
        mapping = {
            "participants": ["Customer", "System", "Database", "Auditor"],
            "messages": [
                {"from": "Customer", "to": "System", "message": "upload document",
                 "source_req_id": "R1"},
                {"from": "System", "to": "Database", "message": "store document",
                 "source_req_id": "R2"},
                {"from": "System", "to": "Auditor", "message": "send audit email",
                 "source_req_id": "R2"},
                {"from": "System", "to": "Customer", "message": "notify user",
                 "source_req_id": "R99"},
            ],
        }
        result = svc._check_compliance(mapping, "sequence", _enriched_requirements())
        kept = {(m["from"], m["message"]) for m in mapping["messages"]}
        exp = enforce_case(CASE)
        exp_kept = {(m["from"], m["text"]) for m in exp["messages"]}
        self.assertEqual(kept, exp_kept)
        # Real rejection count is recorded (not a hardcoded 0).
        self.assertEqual(result["hallucination_rejected_count"], 2)
        self.assertFalse(result["br_11_compliant"])
        self.assertEqual(len(result["rejected_nodes"]), 2)

    def test_production_usecase_matches_experiment(self):
        svc = object.__new__(DiagramGenerationService)
        mapping = {
            "actors": ["Customer", "System", "Database", "Auditor"],
            "use_cases": [
                {"name": "Upload Document", "source_req_id": "R1"},
                {"name": "Invented Feature", "source_req_id": "R99"},
            ],
            "associations": [
                {"actor": "Customer", "use_case": "Upload Document"},
                {"actor": "System", "use_case": "Invented Feature"},
            ],
        }
        result = svc._check_compliance(mapping, "usecase", _enriched_requirements())
        exp = enforce_case(CASE)
        self.assertEqual(set(mapping["actors"]), set(exp["actors"]))
        kept_uc = {uc["name"] for uc in mapping["use_cases"]}
        self.assertEqual(kept_uc, {"Upload Document"})
        # Associations referencing dropped nodes are pruned too.
        self.assertEqual(
            mapping["associations"],
            [{"actor": "Customer", "use_case": "Upload Document"}],
        )
        # 1 use case + 1 actor rejected = 2.
        self.assertEqual(result["hallucination_rejected_count"], 2)

    def test_all_traceable_elements_kept(self):
        """A fully grounded mapping must pass with zero rejections."""
        svc = object.__new__(DiagramGenerationService)
        mapping = {
            "participants": ["Customer", "System"],
            "messages": [
                {"from": "Customer", "to": "System", "message": "upload document",
                 "source_req_id": "R1"},
                {"from": "System", "to": "Customer", "message": "store document",
                 "source_req_id": "R2"},
            ],
        }
        result = svc._check_compliance(mapping, "sequence", _enriched_requirements())
        self.assertEqual(result["hallucination_rejected_count"], 0)
        self.assertTrue(result["br_11_compliant"])
        self.assertEqual(len(mapping["messages"]), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
