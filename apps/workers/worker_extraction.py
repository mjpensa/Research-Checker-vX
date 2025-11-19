"""
Claim Extraction Worker
Processes documents and extracts claims using Gemini API
"""
import asyncio
import logging
import sys
import os
from typing import Dict, Any
from uuid import UUID

# Add packages to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../packages/database'))

from base_worker import BaseWorker
from config import config
from models import Document, Claim, Pipeline, ClaimType, PipelineStatus
import google.generativeai as genai
from datetime import datetime
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Claim extraction prompt template
CLAIM_EXTRACTION_PROMPT = """Extract atomic, verifiable claims from the following research document.

--- BEGIN TEXT ---
{text}
--- END TEXT ---

Source: {source_name}
Source LLM: {source_llm}

Return a JSON object with this exact structure:
{{
  "claims": [
    {{
      "text": "exact claim text",
      "type": "factual|statistical|causal|opinion|hypothesis",
      "confidence": 0.95,
      "evidence_type": "empirical|theoretical|anecdotal",
      "source_span_start": 0,
      "source_span_end": 100,
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

Output ONLY valid JSON. Extract at least 5-10 claims if the text is substantial.
"""

class ClaimExtractionWorker(BaseWorker):
    """Worker for extracting claims from documents"""

    def __init__(self):
        super().__init__("claim-extraction-worker")

        # Configure Gemini
        genai.configure(api_key=config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(config.GEMINI_MODEL)

    async def extract_claims_with_gemini(self, text: str, source_name: str, source_llm: str) -> Dict:
        """Use Gemini to extract claims from text"""

        prompt = CLAIM_EXTRACTION_PROMPT.format(
            text=text[:10000],  # Limit to first 10k chars to avoid token limits
            source_name=source_name,
            source_llm=source_llm or "unknown"
        )

        try:
            logger.info(f"Calling Gemini for claim extraction (text length: {len(text)})")

            # Run in thread pool since genai is sync
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.model.generate_content(
                    prompt,
                    generation_config={
                        'temperature': 0.1,
                        'top_p': 0.95,
                        'max_output_tokens': 8192,
                        'response_mime_type': 'application/json'
                    }
                )
            )

            result = json.loads(response.text)
            logger.info(f"Extracted {len(result.get('claims', []))} claims")

            return result

        except Exception as e:
            logger.error(f"Gemini extraction error: {e}")
            raise

    async def process_job(self, job: Dict) -> Any:
        """Process a claim extraction job"""

        job_id = job['id']
        data = job['data']

        document_id = UUID(data['document_id'])
        pipeline_id = UUID(data['pipeline_id'])

        logger.info(f"Processing claim extraction for document {document_id}")

        async for db in self.get_db():
            try:
                # Get document
                from sqlalchemy import select
                result = await db.execute(
                    select(Document).where(Document.id == document_id)
                )
                document = result.scalar_one_or_none()

                if not document:
                    raise ValueError(f"Document {document_id} not found")

                if not document.extracted_text:
                    raise ValueError(f"Document {document_id} has no extracted text")

                # Update job status
                await self.update_job_status(job_id, 'active', progress=10)

                # Extract claims using Gemini
                result = await self.extract_claims_with_gemini(
                    text=document.extracted_text,
                    source_name=document.filename,
                    source_llm=document.source_llm or "unknown"
                )

                await self.update_job_status(job_id, 'active', progress=50)

                # Save claims to database
                claims_data = result.get('claims', [])
                saved_claims = []

                for claim_data in claims_data:
                    try:
                        # Map claim type
                        claim_type_str = claim_data.get('type', 'factual').upper()
                        try:
                            claim_type = ClaimType[claim_type_str]
                        except KeyError:
                            claim_type = ClaimType.FACTUAL

                        # Create claim
                        claim = Claim(
                            pipeline_id=pipeline_id,
                            document_id=document_id,
                            text=claim_data['text'],
                            claim_type=claim_type,
                            confidence=claim_data.get('confidence', 0.8),
                            evidence_type=claim_data.get('evidence_type'),
                            source_span_start=claim_data.get('source_span_start'),
                            source_span_end=claim_data.get('source_span_end'),
                            surrounding_context=claim_data.get('surrounding_context'),
                            importance_score=0.5,  # Will be calculated later
                            is_foundational=False
                        )

                        db.add(claim)
                        saved_claims.append(claim)

                    except Exception as e:
                        logger.error(f"Error saving claim: {e}")
                        continue

                await db.commit()

                logger.info(f"Saved {len(saved_claims)} claims for document {document_id}")

                # Update document status
                document.status = 'claims_extracted'
                document.processed_at = datetime.utcnow()
                await db.commit()

                # Update pipeline stats
                pipeline_result = await db.execute(
                    select(Pipeline).where(Pipeline.id == pipeline_id)
                )
                pipeline = pipeline_result.scalar_one_or_none()

                if pipeline:
                    from sqlalchemy import func
                    count_result = await db.execute(
                        select(func.count(Claim.id)).where(Claim.pipeline_id == pipeline_id)
                    )
                    total_claims = count_result.scalar()

                    pipeline.total_claims = total_claims
                    pipeline.updated_at = datetime.utcnow()
                    await db.commit()

                await self.update_job_status(job_id, 'active', progress=90)

                return {
                    'document_id': str(document_id),
                    'claims_extracted': len(saved_claims)
                }

            except Exception as e:
                logger.error(f"Error processing job {job_id}: {e}", exc_info=True)
                await db.rollback()
                raise

async def main():
    """Main entry point for the worker"""

    worker = ClaimExtractionWorker()

    try:
        await worker.connect()
        await worker.run('claim_extraction')
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
        worker.stop()
    finally:
        await worker.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
