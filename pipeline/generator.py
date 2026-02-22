import asyncio
from typing import List, AsyncGenerator
from pipeline.retrieval import enhanced_retrieve
from models.llm import vllm_engine
from cache.redis_cache import redis_cache

generation_semaphore = asyncio.Semaphore(3)

CORE_INSTRUCTION = """You are a senior Business Analyst with 15 years of
enterprise software experience. You write formal Business Requirements
Documents for Fortune 500 companies. Your writing is precise, structured,
and professional. Every requirement is numbered, attributed to a source,
and written in formal third-person language. You never mention graph nodes,
entities, chunks, retrieval metadata, or technical pipeline details in your
output. You write directly as the author of a professional document."""

EXECUTIVE_SUMMARY_PROMPT = f"""
{CORE_INSTRUCTION}

The following context has been extracted from real business communications
including emails, meeting transcripts, and messages:

{{context}}

{CORE_INSTRUCTION}

Write a formal Executive Summary section for a Business Requirements Document.
Use this exact structure:

## Executive Summary

### 1.1 Project Overview
One paragraph: what system is being built, for which organization, and the
business purpose. Name the system formally.

### 1.2 Business Context
One paragraph: the business problem or opportunity. Why does this project exist?
What happens if it is not delivered?

### 1.3 Key Stakeholders
| Stakeholder | Title | Primary Role in Project |
|---|---|---|
(populate from communications)

### 1.4 Critical Constraints
Numbered list of the most important constraints on this project:
timeline, budget, resource, technical. Each must cite its source.

### 1.5 In Scope — Phase 1
Bulleted list of what is confirmed in scope for the first phase.

### 1.6 Out of Scope — Deferred
Bulleted list of features explicitly deferred or excluded.

Write now:
"""

BUSINESS_OBJECTIVES_PROMPT = f"""
{CORE_INSTRUCTION}

Context from business communications:
{{context}}

{CORE_INSTRUCTION}

Write the Business Objectives section. Use this structure:

## Business Objectives

### 2.1 Primary Business Goal
One sentence stating the overarching goal of this project.

### 2.2 Strategic Objectives
For each objective found in the communications:

**BO-[N]: [Objective Title]**
- **Statement:** What must be achieved
- **Rationale:** Why this matters to the business
- **Success Measure:** How completion will be verified
- **Source:** Which stakeholder defined this objective

### 2.3 Business Benefits
What measurable value does the business gain upon successful delivery?
Use specific numbers from the communications where available.

Write now:
"""

STAKEHOLDER_ANALYSIS_PROMPT = f"""
{CORE_INSTRUCTION}

Context from business communications:
{{context}}

{CORE_INSTRUCTION}

Write a formal Stakeholder Analysis. Use this structure:

## Stakeholder Analysis

### 3.1 Stakeholder Register

For each named individual in the communications:

#### [Full Name] — [Title]
| Attribute | Detail |
|---|---|
| **Influence** | High / Medium / Low |
| **Interest** | High / Medium / Low |
| **Key Concerns** | What they prioritize |
| **Requirements Owned** | Specific requirements they raised |
| **Known Conflicts** | Disagreements with other stakeholders |

### 3.2 Stakeholder Conflict Register
STRICT RULE FOR CONFLICT REGISTER:
List ONLY conflicts explicitly stated in the source communications.
A conflict exists ONLY when two named people express opposing positions
on the exact same topic in the same email thread.
Maximum 5 conflicts total. When you reach 5, stop immediately.
Do not repeat, rephrase or infer any additional conflicts.
After your last conflict write exactly: "--- End of Conflict Register ---"
Then stop. Generate no more content for this section.

Write now:
"""

FUNCTIONAL_REQUIREMENTS_PROMPT = f"""
{CORE_INSTRUCTION}

Context from business communications:
{{context}}

{CORE_INSTRUCTION}

Write the Functional Requirements section. Every requirement must be
traceable to the source communications. Extract only the most critical
requirements explicitly mentioned in the text (maximum 10 total).

## Functional Requirements

### 4.1 Authentication & Access Control
**FR-001: [Requirement Title]**
- **Description:** The system shall [specific behavior]
- **Source:** [Stakeholder name and communication reference]
- **Priority:** Must Have / Should Have / Nice to Have
- **Acceptance Criteria:** How this will be tested

### 4.2 Performance & Scalability
(Same format, continue requirement numbering)

### 4.3 Dashboard & User Interface
(Same format)

### 4.4 Security & Compliance
(Same format)

### 4.5 Integration Requirements
(Same format)

Write now:
"""

NON_FUNCTIONAL_REQUIREMENTS_PROMPT = f"""
{CORE_INSTRUCTION}

Context from business communications:
{{context}}

{CORE_INSTRUCTION}

Write the Non-Functional Requirements section covering system quality
attributes. Use this structure:

## Non-Functional Requirements

FORMATTING RULE: Every bold marker must open and close on the same line.
Never start a bold marker **like this if you cannot close it on the same line.
Use plain text labels instead: write "Requirement:" not "**Requirement:**" if
the sentence continues to the next line.

For each NFR use this format:
**NFR-[N]: [Quality Attribute] — [Title]**
- **Requirement:** The system shall [measurable quality statement]
- **Metric:** [Specific measurable threshold e.g. 99.9% uptime]
- **Rationale:** Why this level is required
- **Source:** Which communication established this requirement

Cover all of these categories with data from the communications:
- Performance (response time, throughput, concurrent load)
- Availability (uptime, failover, disaster recovery)
- Security (encryption, authentication, audit)
- Scalability (growth capacity, peak load)
- Compliance (regulatory, legal, policy requirements)

Write now:
"""

ASSUMPTIONS_PROMPT = f"""
{CORE_INSTRUCTION}

Context from business communications:
{{context}}

{CORE_INSTRUCTION}

Write the Assumptions, Dependencies and Constraints section:

## Assumptions, Dependencies & Constraints

### 6.1 Assumptions
Numbered list. Each starts with "It is assumed that..."
Only include assumptions explicitly or implicitly present in the
communications. Do not invent assumptions.

### 6.2 Dependencies
What external systems, teams, or decisions must be in place before
this project can proceed or succeed?

### 6.3 Constraints
**Budget Constraints:** Financial limitations stated in communications
**Timeline Constraints:** Hard deadlines and schedule limitations
**Technical Constraints:** Infrastructure or technology limitations
**Resource Constraints:** Staffing or capability limitations explicitly mentioned

### 6.4 Open Issues & Decisions Required
A numbered list of decisions that remain unresolved as of the date of
these communications. Each must reference the specific conflict or
uncertainty from the source material.

Write now:
"""

SUCCESS_METRICS_PROMPT = f"""
{CORE_INSTRUCTION}

Context from business communications:
{{context}}

{CORE_INSTRUCTION}

Write the Success Metrics and KPIs section:

## Success Metrics & KPIs

### 7.1 Key Performance Indicators
For every measurable number found in the communications create a KPI:

**KPI-[N]: [Metric Name]**
| Field | Value |
|---|---|
| **Target Value** | The specific number or threshold |
| **Current Baseline** | Current state if mentioned |
| **Measurement Method** | How this will be tracked |
| **Responsible Owner** | Which stakeholder owns this metric |
| **Review Frequency** | How often measured |
| **Target Date** | When this must be achieved |

### 7.2 Project Acceptance Criteria
The minimum criteria that must ALL be met for project sign-off.
Write as a numbered checklist that a project sponsor could sign.

### 7.3 Definition of Done
One paragraph defining what "complete" means for this project.

Write now:
"""

TIMELINE_PROMPT = f"""
{CORE_INSTRUCTION}

Context from business communications:
{{context}}

{CORE_INSTRUCTION}

Write the Project Timeline section:

## Project Timeline

### 8.1 Phase Overview
For each project phase mentioned in the communications write one
paragraph describing what it includes and its target completion date.

### 8.2 Milestone Schedule
| Milestone ID | Milestone | Description | Target Date | Owner | Dependencies |
|---|---|---|---|---|---|
(Populate from all dates and deadlines in communications)

### 8.3 Timeline Risks
For each date conflict or scheduling disagreement in the communications:

**RISK-[N]: [Risk Title]**
- **Description:** What the scheduling risk is
- **Conflicting Positions:** Who proposed what date
- **Impact if Unresolved:** What slips if this is not decided
- **Resolution Required By:** When a decision must be made

### 8.4 Critical Path
One paragraph identifying which milestones are on the critical path
and the consequences of any delays.

Write now:
"""

SECTION_PROMPTS = {
    "executive_summary": EXECUTIVE_SUMMARY_PROMPT,
    "business_objectives": BUSINESS_OBJECTIVES_PROMPT,
    "stakeholder_analysis": STAKEHOLDER_ANALYSIS_PROMPT,
    "functional_requirements": FUNCTIONAL_REQUIREMENTS_PROMPT,
    "non_functional_requirements": NON_FUNCTIONAL_REQUIREMENTS_PROMPT,
    "assumptions": ASSUMPTIONS_PROMPT,
    "success_metrics": SUCCESS_METRICS_PROMPT,
    "timeline": TIMELINE_PROMPT
}

SECTION_MAX_TOKENS = {
    'executive_summary': 1200,
    'stakeholder_analysis': 1500,  # Hard cap prevents looping
    'functional_requirements': 2000,
    'non_functional_requirements': 1800,
    'business_objectives': 1200,
    'assumptions': 1200,
    'success_metrics': 1500,
    'timeline': 1800
}

CRITICAL_ANTI_HALLUCINATION = """
CRITICAL: Do not invent any project names, company names, system names,
person titles, dates, numbers, or facts not explicitly stated in the source
communications. If a project name is not mentioned, call it "the proposed
platform". If a company name is not mentioned, use the email domain
(e.g. @enron.com = Enron). If a value is unknown write
"Not specified in available communications" — never invent a value.
"""

FORMAT_REQUIREMENTS = """
FORMAT REQUIREMENTS:
Use rich markdown formatting throughout. Every section must include at least
one of the following visual elements where relevant:

- Markdown tables for: stakeholder registers, requirement lists, milestone
  schedules, KPI tracking, comparison matrices
- Mermaid diagrams where helpful:
  * Timeline: use gantt chart
  * Stakeholder relationships: use graph LR
  * Phase dependencies: use flowchart TD

CRITICAL AESTHETICS:
- DO NOT USE ANY EMOJIS EVER. This is a highly professional enterprise document. No emojis.
- DO NOT USE HTML TAGS. Use pure rigorous Markdown. 
- Risk matrices and requirements priority MUST use bold text badges.
  * Example Risk: **[HIGH RISK]**, **[MEDIUM RISK]**, **[LOW RISK]**
  * Example Priority: **[MUST HAVE]**, **[SHOULD HAVE]**, **[NICE TO HAVE]**
  * Example Status: **[CONFIRMED]**, **[AT RISK]**, **[UNRESOLVED]**
- Markdown Tables MUST be perfectly formatted. ALWAYS place a blank newline before and after a table. Make sure every row accurately aligns the `|` pipes.
- Mermaid Diagrams MUST use strict, valid syntax. Close all brackets and parentheses correctly. Do not use experimental Gantt features.
"""

for k in SECTION_PROMPTS:
    section_title_mapped = k.replace('_', ' ').title()
    STOP_INSTRUCTION = f'\nWhen you have completed all subsections of this section, write:\n"--- End of {section_title_mapped} ---"\nand stop generating immediately. Do not add summaries, notes,\nor additional content after this marker.\n'
    SECTION_PROMPTS[k] = SECTION_PROMPTS[k].replace("Write now:", f"{CRITICAL_ANTI_HALLUCINATION}\n{FORMAT_REQUIREMENTS}\n{STOP_INSTRUCTION}\nWrite now:")

PASS_1_PROMPT = """
From the following business communications, extract every concrete fact,
number, date, name, requirement, constraint, and decision. List them as
raw facts only. Be exhaustive.

Communications:
{context}

List all facts:
"""

def format_context(context_chunks: List[str]) -> str:
    """Format the CRAG-filtered chunks into a single readable block."""
    if not context_chunks:
        return "No relevant context found."
    return "\n\n---\n\n".join(context_chunks)

async def generate_brd_section(section_name: str, query: str) -> AsyncGenerator[str, None]:
    # Stream immediately to the UI so it doesn't look frozen while waiting for the Semaphore
    yield f"*(Queueing **{section_name}** for generation...)*\n\n"
    
    async with generation_semaphore:
        yield "*(Retrieving corporate context...)*\n\n"
        # 1. Autonomous Retrieval
        context_chunks = await enhanced_retrieve(query, section_name)
    
        # Check cache hit
        if len(context_chunks) == 2 and context_chunks[0] == "__CACHE_HIT__":
             yield "*(Cache hit! Loading section...)*\n\n"
             yield context_chunks[1]
             return
    
        raw_context = format_context(context_chunks)
        
        # We pass the raw context directly to the final formatting prompt to save 4+ minutes of inference latency
        section_prompt_template = SECTION_PROMPTS.get(section_name, "Write this BRD section.")
        full_prompt = section_prompt_template.format(context=raw_context)
        
        completed_section = ""
        
        yield "*(Synthesizing professional document block...)*\n\n---\n\n"
        
        # Route complex formatting strictly to 32B. Narrative only to 7B Fast Model.
        FAST_SECTIONS = ['executive_summary', 'business_objectives', 'stakeholder_analysis', 'assumptions', 'success_metrics']
        target_model = vllm_engine.draft_model if section_name in FAST_SECTIONS else None
        
        # Limit max_tokens for section to prevent runaway generation
        max_tokens_val = SECTION_MAX_TOKENS.get(section_name, 1800)
        
        section_heading_map = {
            "executive_summary": "## Executive Summary",
            "stakeholder_analysis": "## Stakeholder",
            "functional_requirements": "## Functional",
            "non_functional_requirements": "## Non-Functional",
            "business_objectives": "## Business Objectives",
            "assumptions": "## Assumptions",
            "success_metrics": "## Success Metrics",
            "timeline": "## Timeline"
        }
        
        stop_sequences = [
            "--- End of",
            "CONFLICT-10",  # Hard stop before double digits on conflicts
        ]
        
        for k, v in section_heading_map.items():
            if k != section_name:
                stop_sequences.append(v)
        
        # Standard single pass professional document streaming
        async for token in vllm_engine.generate_stream(full_prompt, temperature=0.3, model_override=target_model, max_tokens=max_tokens_val, stop=stop_sequences):
            completed_section += token
            yield token  # Yield to WebSocket
    
        # Cache the finalized result
        redis_cache.store(query, section_name, completed_section)

async def generate_section_edit(section: str, query: str, current_content: str) -> str:
    """Edits an existing BRD section based on natural language feedback from the user."""
    prompt = f"System: You are an expert business analyst editing a Business Requirements Document. Edit the following section named '{section}' based on the user's request. Output only the revised section content, without any introductory or concluding remarks.\n\nUser Request: {query}\n\nCurrent Content:\n{current_content}\n\nRevised Content:\n"
    
    edited_section = ""
    async for token in vllm_engine.generate_stream(prompt):
        edited_section += token
        
    return edited_section

# Wave 1 — start immediately, highest priority sections (most requested by judges)
WAVE_1 = ['executive_summary', 'functional_requirements', 'stakeholder_analysis']

# Wave 2 — start as soon as ANY Wave 1 section completes
WAVE_2 = ['business_objectives', 'non_functional_requirements', 'assumptions']

# Wave 3 — start as soon as ANY Wave 2 section completes
WAVE_3 = ['success_metrics', 'timeline']

async def generate_full_brd(base_query: str) -> dict:
    async def run_section(section_name):
        full_text = ""
        async for t in generate_brd_section(section_name, base_query):
            full_text += t
        return section_name, full_text

    # Launch Wave 1 — all 3 start simultaneously
    wave1_tasks = [run_section(s) for s in WAVE_1]

    # Launch Wave 2 — starts when semaphore slots free up from Wave 1
    wave2_tasks = [run_section(s) for s in WAVE_2]

    # Launch Wave 3 — starts when semaphore slots free up from Wave 2
    wave3_tasks = [run_section(s) for s in WAVE_3]

    # Gather all — semaphore handles the throttling automatically
    all_tasks = wave1_tasks + wave2_tasks + wave3_tasks
    results = await asyncio.gather(*all_tasks, return_exceptions=True)
    return {sec: txt for sec, txt in results if not isinstance(txt, Exception)}
