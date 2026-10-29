"""Verify manuscript consistency for RQ3."""

import json
import os
from pathlib import Path

REPO_COMMIT = os.environ.get("GIT_COMMIT", "unknown")


def main():
    elements_path = Path("elements.json")
    if not elements_path.exists():
        print("ERROR: elements.json not found")
        return 1

    with open(elements_path) as f:
        elements = json.load(f)

    # Check that elements have required fields
    required_fields = ["case", "condition", "req_text", "actors", "messages", "support_ruleA", "support_ruleB", "grounding_note", "rater"]
    
    issues = []
    for i, e in enumerate(elements):
        for field in required_fields:
            if field not in e:
                issues.append(f"Element {e.get('case', i)}: missing field '{field}'")
    
    # Check condition distribution
    conditions = [e["condition"] for e in elements]
    cond_counts = {c: conditions.count(c) for c in set(conditions)}
    
    # Check that A/B pairs exist
    a_cases = [e["case"] for e in elements if e["condition"] == "A"]
    b_cases = [e["case"] for e in elements if e["condition"] == "B"]
    paired = set(a_cases) & set(b_cases)
    
    front_matter = f"---\ngenerated_by: verify_manuscript_consistency.py\ngenerated_at: {datetime.datetime.utcnow().isoformat()}Z\nrepo_commit: {REPO_COMMIT}\n---\n"
    
    output = front_matter + "# RQ3 Manuscript Consistency Verification\n\n"
    
    if issues:
        output += "## Issues Found\n"
        for issue in issues:
            output += f"- {issue}\n"
    else:
        output += "## Issues Found\n- No issues detected\n"
    
    output += f"\n## Element Statistics\n- Total elements: {len(elements)}\n- Condition distribution: {cond_counts}\n- A/B paired cases: {len(paired)} ({', '.join(sorted(paired)) if paired else 'none'})\n"
    
    # Check for completeness
    expected_pairs = len(set([e["case"] for e in elements]))
    output += f"- Unique case IDs: {expected_pairs}\n"
    
    output_path = Path("paper_assets_final/verify_manuscript_consistency.md")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(output)
    
    print(f"Generated {output_path}")
    return 0


import datetime

if __name__ == "__main__":
    exit(main())