from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class PromptTemplate:
    """Base class for prompt templates"""

    def render(self, **kwargs) -> str:
        """Render template with provided variables"""
        raise NotImplementedError

class ClaimExtractionPrompt(PromptTemplate):
    """Prompt for extracting claims from documents"""

    SYSTEM_PROMPT = """You are a precise claim extraction system. Extract atomic, verifiable claims from research documents.

Rules:
1. Each claim must be a single, testable statement
2. Preserve exact numerical values and dates
3. Maintain source attribution
4. Flag confidence levels based on language used
5. Identify claim type accurately

Output valid JSON only."""

    TEMPLATE = """
Extract claims from the following text:

--- BEGIN TEXT ---
{text}
--- END TEXT ---

Source: {source_name}
Document Type: {document_type}

Return a JSON object with this structure:
{{
  "claims": [
    {{
      "text": "exact claim text",
      "type": "factual|statistical|causal|opinion|hypothesis",
      "confidence": 0.0-1.0,
      "evidence_type": "empirical|theoretical|anecdotal",
      "source_span_start": character_position,
      "source_span_end": character_position,
      "surrounding_context": "brief context around claim"
    }}
  ]
}}

Focus on:
- Factual assertions
- Statistical findings
- Causal relationships
- Key conclusions
- Hypotheses and predictions

Ignore:
- Boilerplate text
- References and citations
- Methodology details (unless they're claims themselves)
"""

    def render(self, text: str, source_name: str, document_type: str = "research") -> str:
        return self.TEMPLATE.format(
            text=text,
            source_name=source_name,
            document_type=document_type
        )

class DependencyAnalysisPrompt(PromptTemplate):
    """Prompt for analyzing dependencies between claims"""

    TEMPLATE = """Analyze the semantic relationship between these two research claims:

Claim A (ID: {claim_a_id}):
Text: "{claim_a_text}"
Type: {claim_a_type}
Source: {claim_a_source}
Context: {claim_a_context}

Claim B (ID: {claim_b_id}):
Text: "{claim_b_text}"
Type: {claim_b_type}
Source: {claim_b_source}
Context: {claim_b_context}

Determine the PRIMARY relationship type and direction:
- CAUSAL: A causes/enables B (or vice versa)
- EVIDENTIAL: A provides evidence for B (or vice versa)
- TEMPORAL: A precedes B chronologically
- PREREQUISITE: B requires A to be true
- CONTRADICTORY: A and B are mutually exclusive
- REFINES: B is a more specific version of A
- NONE: No significant relationship

Consider:
1. Implicit relationships not explicitly stated
2. Domain-specific semantics
3. Logical inference chains
4. Contextual clues from surrounding text

Return ONLY valid JSON:
{{
  "relationship_type": "EVIDENTIAL",
  "direction": "A_to_B|B_to_A|bidirectional",
  "confidence": 0.85,
  "explanation": "Clear reasoning here",
  "semantic_markers": ["keyword1", "keyword2"],
  "strength": "weak|moderate|strong"
}}
"""

    def render(self, claim_a: Dict, claim_b: Dict) -> str:
        return self.TEMPLATE.format(
            claim_a_id=claim_a['id'],
            claim_a_text=claim_a['text'],
            claim_a_type=claim_a.get('type', 'unknown'),
            claim_a_source=claim_a.get('source', 'unknown'),
            claim_a_context=claim_a.get('context', '')[:200],
            claim_b_id=claim_b['id'],
            claim_b_text=claim_b['text'],
            claim_b_type=claim_b.get('type', 'unknown'),
            claim_b_source=claim_b.get('source', 'unknown'),
            claim_b_context=claim_b.get('context', '')[:200],
        )

class ContradictionDetectionPrompt(PromptTemplate):
    """Prompt for detecting contradictions"""

    TEMPLATE = """Analyze these claims for contradictions:

{claims_list}

Consider these types of contradictions:
1. DIRECT: A states X, B states not-X
2. NUMERICAL: Different values for same metric
3. TEMPORAL: Different dates/sequences for same events
4. SCOPE: Universal vs particular claims conflict
5. DEFINITIONAL: Different meanings of same terms

For each contradiction found, return JSON:
{{
  "contradictions": [
    {{
      "claim_a_id": "uuid",
      "claim_b_id": "uuid",
      "type": "direct|numerical|temporal|scope|definitional",
      "severity": "low|medium|high|critical",
      "explanation": "detailed explanation",
      "confidence": 0.0-1.0,
      "resolution_suggestion": "how to resolve if possible"
    }}
  ]
}}
"""

    def render(self, claims: List[Dict]) -> str:
        claims_text = "\n\n".join([
            f"Claim {i+1} (ID: {claim['id']}):\n"
            f"Text: {claim['text']}\n"
            f"Source: {claim.get('source', 'unknown')}\n"
            f"Type: {claim.get('type', 'unknown')}"
            for i, claim in enumerate(claims)
        ])

        return self.TEMPLATE.format(claims_list=claims_text)

class SynthesisPrompt(PromptTemplate):
    """Prompt for generating synthesis reports"""

    TEMPLATE = """Generate an executive synthesis report based on these research claims and their dependencies:

{claims_summary}

Dependency Graph Overview:
{dependency_summary}

Contradictions Found:
{contradictions_summary}

Generate a comprehensive report with these sections:

1. EXECUTIVE SUMMARY
   - High-level overview (2-3 paragraphs)
   - Key takeaways

2. CONSENSUS FINDINGS
   - Claims with multi-source agreement
   - Strength of evidence
   - Foundational claims (cite IDs)

3. KEY INSIGHTS
   - Novel connections discovered
   - Emergent patterns
   - Cross-source synthesis

4. DISPUTED AREAS
   - Contradictions requiring resolution
   - Evidence gaps
   - Areas of uncertainty

5. DEPENDENCY ANALYSIS
   - Critical dependency chains
   - Foundational vs derived claims
   - Vulnerability analysis

6. RECOMMENDATIONS
   - Next research steps
   - Areas needing clarification
   - Priority questions

Format the report in Markdown. Use clear, professional language. Cite claim IDs inline like [Claim: abc-123].
"""

    def render(
        self,
        claims_summary: str,
        dependency_summary: str,
        contradictions_summary: str
    ) -> str:
        return self.TEMPLATE.format(
            claims_summary=claims_summary,
            dependency_summary=dependency_summary,
            contradictions_summary=contradictions_summary
        )
