"""
Professional Requirements Extraction & Analysis Prompts.
Engineering-grade prompts designed to extract clean, atomic requirements while
strictly filtering document noise (TOC, figures, tables, section headers).
"""

REQUIREMENT_EXTRACTION_PROMPT = """You are a highly strict Automated Requirements Extraction Engine. Your sole purpose is to scan raw document text, isolate individual software requirements, and discard 100% of the surrounding context.

CRITICAL DIRECTIVES (YOU MUST OBEY THESE OR FAIL):
1. THE KEYWORD RULE: A valid requirement MUST contain at least one of these modal verbs: "shall", "must", "should", or "will". If a sentence does not contain one of these words, YOU MUST IGNORE IT COMPLETELY.
2. THE BAN LIST: You must NEVER output sentences that contain the following boilerplate words: "Figure", "Table", "Section", "Appendix", "This document details", "As shown in", "Sequence Diagram".
3. THE ATOMIC RULE: You must isolate the core rule. Maximum length is 2 sentences. NEVER output a whole paragraph.
4. SPLIT COMPOUND RULES: If a paragraph contains multiple "shall" or "must" statements, split them into separate JSON objects.
5. CLEAN TEXT RULE: You must remove all markdown formatting (like **, ##, `) and stray unicode characters from your output. Provide ONLY plain, professional, readable English.

EXAMPLES OF YOUR TASK:
Bad Raw Text: "The system must operate 24/7. 4.3 Reliability. Table 63 Business Rules. Section 5 Summary. This document details the software requirement specification."
Correct Output: "The system must operate 24/7." (Notice everything after the core rule was instantly deleted).

Bad Raw Text: "The system shall interface with a payment gateway. For offline consultation, payments shall be via cash. Table 6 Sign In."
Correct Output (Split into two objects): 
Object 1: "The system shall interface with a payment gateway."
Object 2: "For offline consultation, payments shall be via cash."

OUTPUT SCHEMA (JSON Array Only):
[
  {{
    "module_name": "String (Determine from context, e.g., 'System Deployment', 'Payment', 'User Management')",
    "category": "String (Strictly ONE of: functional, non_functional, interface, constraint, data)",
    "semantic_id": "String (e.g., FR-DEP-01 for Deployment, NFR-PERF-01 for Performance)",
    "original_text": "String (THE ISOLATED, CLEANED REQUIREMENT ONLY. MAX 2 SENTENCES.)",
    "actors": ["String (Extract implied actors, e.g., 'System', 'Patient', 'Admin')"]
  }}
]

Raw Text to Scan:
{text}"""

CLASSIFICATION_PROMPT = """You are a Requirements Classification Specialist. Classify each requirement using IEEE 830 standards.

CATEGORIES WITH STRICT DEFINITIONS:
- functional: System behaviors, features, capabilities (what system SHALL DO)
- non_functional: Performance, scalability, availability, reliability, maintainability, portability, usability, backup/recovery, SLAs, response time, throughput, capacity, resource limits
- interface: User interfaces, APIs, hardware/software interactions
- constraint: Technical, regulatory, business limitations
- data: Data storage, format, structure requirements

CLASSIFICATION RULES:
- If requirement describes an ACTION or BEHAVIOR → functional
- If requirement describes PERFORMANCE METRICS, QUALITY ATTRIBUTES, uptime, backup, security posture (non-behavioral quality) → non_functional
- If requirement describes INTERACTION POINT → interface
- If requirement describes LIMITATION or RESTRICTION → constraint
- If requirement describes DATA handling → data

EXAMPLES (follow strictly):
- "The system shall respond within 2 seconds" → non_functional
- "The system shall encrypt data at rest using AES-256" → non_functional
- "The system shall provide login" → functional

Return JSON only:
{{
  "classifications": [
    {{
      "text": "exact requirement text",
      "category": "functional|non_functional|interface|constraint|data",
      "confidence": 0.0-1.0,
      "rationale": "brief justification"
    }}
  ]
}}

Requirements to classify:
{text}
"""

ENTITY_EXTRACTION_PROMPT = """You are an Entity Extraction Specialist. Identify actors, systems, and key terms from requirements.

EXTRACTION RULES:
- ACTORS: Users, roles, external systems that interact with the system
- SYSTEMS: Software components, databases, services
- MODAL VERBS: shall, must, should, may, will (indicate requirement strength)
- VAGUE TERMS: subjective, immeasurable, unclear terms

STRICT FILTERING:
- Ignore document structure elements
- Ignore table/figure references
- Only extract entities mentioned in actual requirement statements

Return JSON only:
{{
  "entities": [
    {{
      "name": "entity_name",
      "type": "actor|system|component|data",
      "description": "brief role/purpose"
    }}
  ],
  "modal_verbs": ["shall", "must", "should", "may", "will"],
  "vague_terms": ["efficient", "user-friendly", "appropriate", "fast", "sufficient"],
  "confidence": 0.0-1.0
}}

Requirements text to analyze:
{text}
"""

AMBIGUITY_DETECTION_PROMPT = """You are a Requirements Quality Specialist. Detect ONLY CRITICAL ambiguous, vague, or defective requirements. Be lenient for academic/student projects.

DEFECT TYPES WITH PRECISE DEFINITIONS (FLAG ONLY CRITICAL ISSUES):
- ambiguity: CRITICAL pronoun issues (it, they, this) with NO clear context, severe multiple interpretations
- incompleteness: MISSING essential functionality or MAJOR missing conditions
- inconsistency: DIRECT contradictions between requirements
- unverifiable: COMPLETELY impossible to test or measure

SEVERITY GUIDELINES (BE CONSERVATIVE):
- HIGH: Only for critical issues that make requirement unusable
- MEDIUM: For significant clarity problems that affect implementation
- LOW: For minor improvements that would be nice to have

DETECTION RULES (balanced):
- FLAG subjective or unmeasurable wording (e.g. "user-friendly", "adequate", "appropriate", "reasonable", "fast", "scalable" without metrics) as ambiguity with severity MEDIUM unless it blocks all interpretation (then HIGH).
- FLAG missing acceptance criteria for quality attributes (performance, security, usability) as incompleteness MEDIUM when confidence >= 0.70.
- Do not flood: aim for meaningful defects; merge duplicates.

Return JSON only (defects should be < 40% of lines unless text is genuinely poor quality):
{
  "defects": [
    {
      "text": "exact problematic text",
      "type": "ambiguity|incompleteness|inconsistency|unverifiable",
      "severity": "high|medium|low",
      "confidence": 0.0-1.0,
      "description": "clear explanation of the issue",
      "suggestion": "specific improvement recommendation"
    }
  ]
}

Requirements to analyze:
{text}
"""

COMPLEXITY_ESTIMATION_PROMPT = """You are a Technical Estimation Specialist. Analyze implementation complexity for requirements.

COMPLEXITY FACTORS:
- Actor count and interaction complexity
- Conditional logic and decision branches
- Data validation and transformation requirements
- External system integrations
- Security and compliance requirements
- Performance constraints and scalability needs
- User interface complexity

SCORING CRITERIA:
- 0-25: Low complexity (simple CRUD, single actor)
- 26-50: Medium complexity (multiple actors, basic logic)
- 51-75: High complexity (integrations, complex workflows)
- 76-100: Critical complexity (real-time, high security, scaling)

Return JSON only:
{{
  "complexity_score": 0-100,
  "estimated_effort_hours": number,
  "risk_level": "low|medium|high|critical",
  "factors": [
    {{
      "factor": "specific complexity factor",
      "impact": "low|medium|high",
      "description": "why this adds complexity"
    }}
  ],
  "recommendations": ["specific suggestions to reduce complexity"]
}}

Requirements to estimate:
{text}
"""

VALIDATION_PROMPT = """You are a requirements engineering expert following IEEE 830 standards. Analyze the following requirement and return a JSON object.

Requirement: {requirement_text}

Evaluate for the four IEEE 830 defect types:
1. Ambiguity: vague terms (e.g., "fast", "adequate", "user-friendly", "appropriate", "reasonable") that have multiple interpretations
2. Incompleteness: missing conditions, exceptions, error handling, or constraints
3. Inconsistency: contradictions with standard requirements engineering practices
4. Unverifiability: no measurable acceptance criteria or test conditions

For each defect found, provide:
- type (string): one of "ambiguity", "incompleteness", "inconsistency", "unverifiable"
- severity (string): "High", "Medium", or "Low"
- confidence (float): 0.0-1.0 (only include defects with confidence >= 0.70)
- suggestion (string): concrete rewrite recommendation with specific, measurable criteria

Return JSON format:
{{
  "defects": [
    {{
      "type": "ambiguity|incompleteness|inconsistency|unverifiable",
      "severity": "High|Medium|Low",
      "confidence": 0.0-1.0,
      "suggestion": "specific rewrite recommendation"
    }}
  ]
}}

Only include defects with confidence >= 0.70. If no defects meet this threshold, return empty defects array.
"""

DIAGRAM_GENERATION_PROMPT = """You are a Technical Visualization Specialist. Generate clean Mermaid diagrams from requirements.

DIAGRAM STANDARDS:
- Use clear, descriptive names for actors and components
- Follow proper Mermaid syntax for the specified diagram type
- Include only essential interactions, avoid clutter
- Ensure logical flow and readability

USE CASE DIAGRAM SYNTAX:
```mermaid
usecaseDiagram
  actor ActorName as "Actor Display Name"
  usecase "Use Case Description" as UC1
  ActorName --> UC1
```

SEQUENCE DIAGRAM SYNTAX:
```mermaid
sequenceDiagram
  participant A as Actor
  participant S as System
  A->>S: Action Description
  S-->>A: Response Description
```

Return ONLY the complete mermaid code block. No explanations or extra text.

Requirements:
{text}

Diagram type: {diagram_type}
"""


IEEE_USECASE_EXTRACTION_PROMPT = """You are an expert in IEEE 29148 and UML 2.5 standards.
Extract ONLY structured Use Case mapping data from requirements text.

STRICT RULES:
1. Actors must represent users or external systems.
2. Use cases must be actionable system functions.
3. Associations must map Actor -> UseCase and should cover all listed use cases whenever possible.
4. Include/extend relations must be output as dependency pairs.
5. No conversational text, no markdown, no code fences.
6. Return ONLY valid JSON matching this schema.

JSON SCHEMA:
{{
  "actors": ["Actor1", "Actor2"],
  "use_cases": ["UseCase1", "UseCase2"],
  "includes": [["BaseUC", "IncludedUC"]],
  "extends": [["BaseUC", "ExtendingUC"]],
  "associations": [["Actor", "UseCase"]]
}}

TEXT:
{text}
"""
