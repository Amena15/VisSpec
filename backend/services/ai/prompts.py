"""
Few-shot prompting templates for LLaMA 3 requirement analysis.
Based on IEEE 830 standards for software requirements specification.
"""

AMBIGUITY_DETECTION_PROMPT = """You are a requirements analyst. Detect ambiguous, vague, or defective requirements.

Rules:
- Flag pronouns without clear antecedents (it, they, this, these)
- Flag subjective terms (user-friendly, efficient, fast, appropriate)
- Flag incomplete conditions or missing edge cases
- Flag contradictory statements
- Flag unverifiable requirements (no measurable criteria)

Return JSON only:
{{
  "defects": [
    {{
      "text": "the defective sentence",
      "type": "ambiguity|incompleteness|inconsistency|unverifiable",
      "severity": "high|medium|low",
      "confidence": 0.0-1.0,
      "description": "explanation of the defect",
      "suggestion": "how to fix it"
    }}
  ]
}}

Requirements to analyze:
{text}
"""

CLASSIFICATION_PROMPT = """Classify each requirement according to IEEE 830 categories.

Categories:
- functional: What the system shall do
- non_functional: Performance, security, usability constraints
- interface: User interface, API, hardware interfaces
- constraint: Technical, regulatory, or business constraints
- data: Data storage, format, or structure requirements

Return JSON only:
{{
  "classifications": [
    {{
      "text": "the requirement text",
      "category": "functional|non_functional|interface|constraint|data",
      "confidence": 0.0-1.0
    }}
  ]
}}

Requirements to classify:
{text}
"""

ENTITY_EXTRACTION_PROMPT = """Extract entities, actors, and relationships from requirements text.

Return JSON only:
{{
  "entities": [
    {{
      "text": "entity name",
      "type": "actor|system|component|data|external_system",
      "description": "brief description"
    }}
  ],
  "relationships": [
    {{
      "source": "entity name",
      "target": "entity name",
      "type": "uses|creates|validates|sends_to|receives_from",
      "description": "relationship description"
    }}
  ],
  "modal_verbs": ["shall", "should", "may", "must"],
  "vague_terms": ["list of vague terms found"]
}}

Text to analyze:
{text}
"""

COMPLEXITY_ESTIMATION_PROMPT = """Estimate the complexity of implementing these requirements.

Consider:
- Number of actors and their interactions
- Conditional logic complexity
- Data validation requirements
- Integration points with external systems
- Security and compliance requirements
- Performance constraints

Return JSON only:
{{
  "complexity_score": 0-100,
  "estimated_effort_hours": number,
  "risk_level": "low|medium|high|critical",
  "factors": [
    {{
      "factor": "description of complexity factor",
      "impact": "low|medium|high"
    }}
  ],
  "recommendations": ["list of recommendations to reduce complexity"]
}}

Requirements to estimate:
{text}
"""

DIAGRAM_GENERATION_PROMPT = """Generate a Mermaid diagram from the following requirements.

For use case diagrams, use this syntax:
```mermaid
usecaseDiagram
  actor ActorName
  usecase "Use Case Description" as UC1
  ActorName --> UC1
```

For sequence diagrams, use this syntax:
```mermaid
sequenceDiagram
  participant A as Actor
  participant S as System
  A->>S: Action
  S-->>A: Response
```

Return ONLY the mermaid code block, nothing else.

Requirements:
{text}

Diagram type: {diagram_type}
"""
