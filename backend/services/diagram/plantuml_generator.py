"""
IEEE-Compliant PlantUML Generator.
Generates standard UML 2.5 diagrams with proper notation.
"""
import re
from typing import Dict, List, Any
from backend.core.logging import get_logger

logger = get_logger(__name__)


class PlantUMLGenerator:
    """Generates IEEE-compliant PlantUML syntax for all diagram types."""

    def _shorten_name(self, name: str) -> str:
        clean = re.sub(r'[^a-zA-Z0-9]', '', name)
        if len(clean) > 8:
            clean = clean[:8]
        return clean.upper() if clean else 'X'

    def _sanitize_plantuml_text(self, text: str) -> str:
        """Sanitize free-form text for PlantUML compatibility."""
        if not text:
            return ""

        cleaned = str(text)
        cleaned = re.sub(r'#+', '', cleaned)  # markdown headings
        cleaned = re.sub(r'[*_]{1,2}', '', cleaned)  # bold/italic markers
        cleaned = re.sub(r'`[^`]+`', '', cleaned)  # inline code
        cleaned = re.sub(r'<[^>]+>', '', cleaned)  # html tags
        cleaned = cleaned.replace('"', "'")
        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned.strip()

    def _clean_text(self, text: str) -> str:
        """Backward-compatible cleaner used by existing call sites."""
        return self._sanitize_plantuml_text(text)

    def _norm_key(self, text: str) -> str:
        """Normalize text for resilient cross-reference matching."""
        return re.sub(r'[^a-z0-9]+', '', (text or '').lower())

    def generate_usecase_plantuml(self, data: Dict[str, Any]) -> str:
        """Generate IEEE-standard Use Case diagram PlantUML."""
        actors = data.get("actors", [])
        use_cases = data.get("use_cases", [])
        associations = data.get("associations", [])
        includes = data.get("includes", [])
        extends_ = data.get("extends", [])
        system_name = self._clean_text(data.get("system_name", "System"))

        # Clean actor and use case names
        actor_names = []
        for a in actors:
            if isinstance(a, dict):
                actor_names.append(self._clean_text(a.get('name', str(a))))
            else:
                actor_names.append(self._clean_text(str(a)))
        actor_names = [a for a in actor_names if a]

        # Keep actor list aligned with association payload so edges are not lost.
        assoc_actor_names = []
        for assoc in associations or []:
            if isinstance(assoc, dict):
                assoc_actor_names.append(self._clean_text(assoc.get('actor')))
            elif isinstance(assoc, (list, tuple)) and len(assoc) >= 2:
                assoc_actor_names.append(self._clean_text(assoc[0]))
        for assoc_actor in assoc_actor_names:
            if assoc_actor and assoc_actor not in actor_names:
                actor_names.append(assoc_actor)

        use_case_names = []
        for uc in use_cases:
            if isinstance(uc, dict):
                use_case_names.append(self._clean_text(uc.get('name', str(uc))))
            else:
                use_case_names.append(self._clean_text(str(uc)))
        use_case_names = [u for u in use_case_names if u]

        lines = [
            "@startuml",
            "!theme plain",
            "",
            f'title {system_name} - Use Case Diagram',
            "",
            "' IEEE Standard Styling",
            "skinparam actorStyle stickman",
            "skinparam packageStyle rectangle",
            "skinparam usecase {",
            "  BackgroundColor #FFFFFF",
            "  BorderColor #000000",
            "  FontColor #000000",
            "}",
            "left to right direction",
            "",
            "' === ACTORS (outside the system boundary) ===",
        ]

        actor_ids = {}
        for i, name in enumerate(actor_names):
            actor_id = f"A{i}"
            actor_ids[name] = actor_id
            if name.lower() in ["system", "external system"]:
                lines.append(f'actor "{name}" as {actor_id} <<System>>')
            else:
                lines.append(f'actor "{name}" as {actor_id}')

        lines.append("")
        lines.append("' === SYSTEM BOUNDARY ===")
        lines.append(f"rectangle \"{system_name}\" {{")

        uc_ids = {}
        for i, name in enumerate(use_case_names):
            uc_id = f"UC{i}"
            uc_ids[name] = uc_id
            lines.append(f"    usecase \"{name}\" as {uc_id}")

        lines.append("}")

        if includes:
            lines.append("")
            lines.append("' === INCLUDE RELATIONSHIPS ===")
            for base, included in includes:
                base = self._clean_text(base)
                included = self._clean_text(included)
                if base in uc_ids and included in uc_ids:
                    lines.append(f"{uc_ids[base]} .> {uc_ids[included]} : <<include>>")

        if extends_:
            lines.append("")
            lines.append("' === EXTEND RELATIONSHIPS ===")
            for base, extending in extends_:
                base = self._clean_text(base)
                extending = self._clean_text(extending)
                if base in uc_ids and extending in uc_ids:
                    lines.append(f"{uc_ids[extending]} .> {uc_ids[base]} : <<extend>>")

        lines.append("")
        lines.append("' === ACTOR ASSOCIATIONS ===")
        actor_lookup = {self._norm_key(k): k for k in actor_ids}
        uc_lookup = {self._norm_key(k): k for k in uc_ids}
        resolved_associations = []

        for assoc in associations or []:
            if isinstance(assoc, dict):
                actor_name = self._clean_text(assoc.get('actor'))
                uc_name = self._clean_text(assoc.get('use_case'))
            elif isinstance(assoc, (list, tuple)) and len(assoc) >= 2:
                actor_name = self._clean_text(assoc[0])
                uc_name = self._clean_text(assoc[1])
            else:
                continue

            actor_key = actor_lookup.get(self._norm_key(actor_name))
            uc_key = uc_lookup.get(self._norm_key(uc_name))
            if actor_key and uc_key:
                resolved_associations.append((actor_key, uc_key))

        # Fallback: guarantee visible connectors (strict UML readability).
        if not resolved_associations and actor_names and use_case_names:
            for i, uc in enumerate(use_case_names):
                actor = actor_names[i % len(actor_names)]
                resolved_associations.append((actor, uc))

        seen_assoc = set()
        for actor_name, uc_name in resolved_associations:
            k = (actor_name, uc_name)
            if k in seen_assoc:
                continue
            seen_assoc.add(k)
            lines.append(f"{actor_ids[actor_name]} -- {uc_ids[uc_name]}")

        # Strict guarantee: every use case must be connected to at least one actor.
        connected_uc_names = {uc for _, uc in seen_assoc}
        if actor_names:
            primary_actor = actor_names[0]
            for uc_name in use_case_names:
                if uc_name not in connected_uc_names:
                    lines.append(f"{actor_ids[primary_actor]} -- {uc_ids[uc_name]}")
                    seen_assoc.add((primary_actor, uc_name))
                    connected_uc_names.add(uc_name)

        # Strict guarantee: every actor must be connected to at least one use case.
        connected_actor_names = {actor for actor, _ in seen_assoc}
        if use_case_names:
            primary_use_case = use_case_names[0]
            for actor_name in actor_names:
                if actor_name not in connected_actor_names:
                    lines.append(f"{actor_ids[actor_name]} -- {uc_ids[primary_use_case]}")
                    seen_assoc.add((actor_name, primary_use_case))
                    connected_actor_names.add(actor_name)

        lines.append("")
        lines.append("@enduml")
        return "\n".join(lines)

    def generate_sequence_plantuml(self, data: Dict[str, Any]) -> str:
        """Generate IEEE-standard Sequence diagram PlantUML."""
        participants = data.get("participants", [])
        messages = data.get("messages", [])
        scenario = self._clean_text(data.get("scenario", "Sequence Diagram"))
        truncated = data.get("truncated", False)

        lines = [
            "@startuml",
            "!theme plain",
            "",
            f'title {scenario}',
            "",
            "' Sequence diagram styling",
            "skinparam sequenceMessageAlignment center",
            "skinparam sequence {",
            "  ParticipantPadding 20",
            "  MessagePadding 10",
            "}",
            "",
            "' === PARTICIPANTS ===",
        ]

        participant_ids = {}
        for i, participant in enumerate(participants):
            pid = f"P{i}"
            if isinstance(participant, dict):
                name = self._clean_text(participant.get("name", ""))
            else:
                name = self._clean_text(participant)
            if not name:
                continue
            participant_ids[name] = pid
            if name.lower() not in ["system", "database", "server", "api"]:
                lines.append(f'actor "{name}" as {pid}')
            else:
                lines.append(f'participant "{name}" as {pid}')

        lines.append("")
        lines.append("' === MESSAGES ===")

        active_participants = set()

        normalized_messages = []
        for msg in messages or []:
            if not isinstance(msg, dict):
                continue
            from_p = self._clean_text(msg.get("from", ""))
            to_p = self._clean_text(msg.get("to", ""))
            message = self._clean_text(msg.get("message", ""))

            # Fallback routing for incomplete message objects.
            if not from_p and participant_ids:
                from_p = next(iter(participant_ids.keys()))
            if not to_p and len(participant_ids) >= 2:
                to_p = list(participant_ids.keys())[1]
            if not message:
                message = "Perform action"

            normalized_messages.append({
                "from": from_p,
                "to": to_p,
                "message": message,
            })

        # Fallback: guarantee at least one interaction arrow.
        if not normalized_messages and len(participant_ids) >= 2:
            names = list(participant_ids.keys())
            normalized_messages.append({
                "from": names[0],
                "to": names[1],
                "message": "Request operation",
            })

        for idx, msg in enumerate(normalized_messages):
            from_p = msg["from"]
            to_p = msg["to"]
            message = msg["message"]

            if from_p in participant_ids and to_p in participant_ids:
                from_id = participant_ids[from_p]
                to_id = participant_ids[to_p]

                if to_p not in active_participants:
                    lines.append(f'activate {to_id}')
                    active_participants.add(to_p)

                lines.append(f'{from_id} -> {to_id} : {message}')

                # Deactivate if no more messages to this participant
                next_messages = [m for m in normalized_messages[idx + 1:] if m.get("to") == to_p]
                if not next_messages:
                    lines.append(f'deactivate {to_id}')
                    active_participants.discard(to_p)

        for participant in list(active_participants):
            if participant in participant_ids:
                lines.append(f'deactivate {participant_ids[participant]}')

        if truncated:
            lines.append("")
            lines.append("note right of P0")
            lines.append("  <color:red>BR-12: Diagram truncated to 15 steps</color>")
            lines.append("end note")

        lines.append("")
        lines.append("@enduml")
        return "\n".join(lines)

    def generate_activity_plantuml(self, data: Dict[str, Any]) -> str:
        """Generate IEEE-standard Activity diagram PlantUML."""
        activities = data.get("activities", [])
        decisions = data.get("decisions", [])
        flow = data.get("flow", [])

        lines = [
            "@startuml",
            "!theme plain",
            "",
            "title Activity Diagram",
            "",
            "' Activity diagram styling",
            "skinparam activity {",
            "  BackgroundColor #FFFFFF",
            "  BorderColor #000000",
            "  FontColor #000000",
            "}",
            "",
            "start",
        ]

        # Add activities
        activity_ids = {}
        for i, activity in enumerate(activities):
            aid = f"Act{i}"
            activity_ids[activity] = aid
            lines.append(f":{activity};")

        # Add decisions
        for decision in decisions:
            condition = decision.get("condition", "Decision")
            yes_branch = decision.get("yes", "End")
            no_branch = decision.get("no", "End")

            lines.append(f"if ({condition}) then")
            lines.append(f"  :{yes_branch};")
            lines.append("else")
            lines.append(f"  :{no_branch};")
            lines.append("endif")

        # Add flow
        for from_step, to_step in flow:
            if from_step in activity_ids and to_step in activity_ids:
                lines.append(f"{activity_ids[from_step]} --> {activity_ids[to_step]}")

        lines.append("")
        lines.append("end")
        lines.append("@enduml")

        return "\n".join(lines)