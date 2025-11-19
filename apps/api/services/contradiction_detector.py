"""
Contradiction Detection Service
Identifies conflicting claims within a pipeline
"""
import logging
from typing import List, Dict
import sys
import os

# Add packages to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../packages/database'))

from services.gemini.client import gemini_client
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import Claim, Contradiction, Pipeline
from uuid import uuid4
from datetime import datetime

logger = logging.getLogger(__name__)

CONTRADICTION_PROMPT = """Analyze these research claims for contradictions:

{claims_list}

Look for these types of contradictions:
1. DIRECT: Claims state opposite facts
2. NUMERICAL: Different values for the same metric
3. TEMPORAL: Conflicting dates or time sequences
4. SCOPE: Universal vs particular claims in conflict
5. DEFINITIONAL: Different meanings of the same term

For each contradiction found, return JSON:
{{
  "contradictions": [
    {{
      "claim_a_id": "uuid-here",
      "claim_b_id": "uuid-here",
      "type": "direct|numerical|temporal|scope|definitional",
      "severity": "low|medium|high|critical",
      "explanation": "detailed explanation",
      "confidence": 0.9,
      "resolution_suggestion": "how to resolve if possible"
    }}
  ]
}}

Only include high-confidence contradictions (confidence > 0.7).
If no contradictions found, return {{"contradictions": []}}
"""

class ContradictionDetector:
    """Service for detecting contradictions between claims"""

    def __init__(self):
        self.min_confidence = 0.7

    async def detect_contradictions(
        self,
        pipeline_id: str,
        db: AsyncSession,
        max_claims: int = 50
    ) -> List[Dict]:
        """Detect contradictions in pipeline claims"""

        logger.info(f"Detecting contradictions for pipeline {pipeline_id}")

        # Fetch claims (prioritize important claims)
        result = await db.execute(
            select(Claim)
            .where(Claim.pipeline_id == pipeline_id)
            .order_by(Claim.importance_score.desc())
            .limit(max_claims)
        )
        claims = result.scalars().all()

        if len(claims) < 2:
            logger.warning("Not enough claims for contradiction detection")
            return []

        # Format claims for prompt
        claims_text = "\n\n".join([
            f"Claim {i+1} (ID: {claim.id}):\n"
            f"Text: {claim.text}\n"
            f"Source: Document {claim.document_id}\n"
            f"Type: {claim.claim_type.value if claim.claim_type else 'unknown'}"
            for i, claim in enumerate(claims)
        ])

        prompt = CONTRADICTION_PROMPT.format(claims_list=claims_text)

        try:
            # Call Gemini for contradiction detection
            result = await gemini_client.generate_json_async(
                prompt,
                use_cache=False  # Don't cache contradiction detection
            )

            contradictions = result.get('contradictions', [])

            logger.info(f"Found {len(contradictions)} potential contradictions")

            # Filter by confidence
            high_conf_contradictions = [
                c for c in contradictions
                if c.get('confidence', 0) >= self.min_confidence
            ]

            logger.info(f"Keeping {len(high_conf_contradictions)} high-confidence contradictions")

            return high_conf_contradictions

        except Exception as e:
            logger.error(f"Error detecting contradictions: {e}", exc_info=True)
            return []

    async def save_contradictions(
        self,
        pipeline_id: str,
        contradictions: List[Dict],
        db: AsyncSession
    ) -> int:
        """Save detected contradictions to database"""

        saved_count = 0

        for contra in contradictions:
            try:
                contradiction = Contradiction(
                    pipeline_id=pipeline_id,
                    claim_a_id=contra['claim_a_id'],
                    claim_b_id=contra['claim_b_id'],
                    contradiction_type=contra.get('type', 'direct'),
                    severity=contra.get('severity', 'medium'),
                    explanation=contra.get('explanation', ''),
                    resolution_suggestion=contra.get('resolution_suggestion'),
                    confidence=contra.get('confidence', 0.8),
                    supporting_evidence={
                        'detection_method': 'gemini_analysis',
                        'detected_at': datetime.utcnow().isoformat()
                    }
                )

                db.add(contradiction)
                saved_count += 1

            except Exception as e:
                logger.error(f"Error saving contradiction: {e}")
                continue

        await db.commit()

        # Update pipeline stats
        pipeline_result = await db.execute(
            select(Pipeline).where(Pipeline.id == pipeline_id)
        )
        pipeline = pipeline_result.scalar_one_or_none()

        if pipeline:
            # Count total contradictions
            from sqlalchemy import func
            count_result = await db.execute(
                select(func.count(Contradiction.id))
                .where(Contradiction.pipeline_id == pipeline_id)
            )
            total_contradictions = count_result.scalar()

            pipeline.total_contradictions = total_contradictions
            pipeline.updated_at = datetime.utcnow()
            await db.commit()

        logger.info(f"Saved {saved_count} contradictions to database")

        return saved_count

contradiction_detector = ContradictionDetector()
