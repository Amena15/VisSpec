"""Generate reproducibility evidence markdown file for RQ3."""

import datetime
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

    total_elements = len(elements)
    conditions = {"A": 0, "B": 0}
    for e in elements:
        conditions[e["condition"]] = conditions.get(e["condition"], 0) + 1

    front_matter = f"""---\ngenerated_by: generate_reproducibility_evidence.py\ngenerated_at: {datetime.datetime.utcnow().isoformat()}Z\nrepo_commit: {REPO_COMMIT}\n---\n"""

    # Count supported/unsupported per rule
    rule_counts = {"support_ruleA": {"supported": 0, "unsupported": 0}, "support_ruleB": {"supported": 0, "unsupported": 0}}

    for e in elements:
        for rule in ["support_ruleA", "support_ruleB"]:
            flag = e.get(rule, [False])[0] if e.get(rule) else False
            if flag:
                rule_counts[rule]["supported"] += 1
            else:
                rule_counts[rule]["unsupported"] += 1

    output = front_matter + f"\n# RQ3 Reproducibility Evidence\n\n## Summary\n- Total elements: {total_elements}\n- Condition A: {conditions.get('A', 0)} elements\n- Condition B: {conditions.get('B', 0)} elements\n\n## Rule A Grounding Summary\n- Supported: {rule_counts['support_ruleA']['supported']}\n- Unsupported: {rule_counts['support_ruleA']['unsupported']}\n\n## Rule B Grounding Summary\n- Supported: {rule_counts['support_ruleB']['supported']}\n- Unsupported: {rule_counts['support_ruleB']['unsupported']}\n"""

    output_path = Path("paper_assets_final/reproducibility_evidence.md")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(output)

    print(f"Generated {output_path} with {total_elements} elements")
    return 0


if __name__ == "__main__":
    exit(main())