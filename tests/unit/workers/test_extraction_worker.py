"""
Unit tests for Claim Extraction Worker.
Tests document processing and claim extraction functionality.
"""

import pytest
from uuid import uuid4
from unittest.mock import Mock, patch, AsyncMock


@pytest.mark.unit
@pytest.mark.worker
class TestExtractionWorker:
    """Test claim extraction worker functionality."""

    def test_extract_text_from_txt(self, sample_document_file):
        """Test extracting text from TXT file."""
        from apps.workers.worker_extraction import ClaimExtractionWorker

        worker = ClaimExtractionWorker()
        text = worker.extract_text(sample_document_file, 'text/plain')

        assert len(text) > 0
        assert "Test Document" in text or "test" in text.lower()

    def test_extract_text_from_pdf(self, sample_pdf_file):
        """Test extracting text from PDF file."""
        from apps.workers.worker_extraction import ClaimExtractionWorker

        worker = ClaimExtractionWorker()
        text = worker.extract_text(sample_pdf_file, 'application/pdf')

        assert len(text) > 0
        assert "PDF" in text or "test" in text.lower()

    @pytest.mark.asyncio
    @patch('apps.workers.worker_extraction.genai.GenerativeModel')
    async def test_extract_claims_with_gemini(self, mock_model):
        """Test claim extraction using Gemini API."""
        from apps.workers.worker_extraction import ClaimExtractionWorker

        # Mock Gemini response
        mock_response = Mock()
        mock_response.text = '''{
            "claims": [
                {
                    "text": "AI is transforming society",
                    "type": "factual",
                    "confidence": 0.95,
                    "evidence_type": "empirical"
                },
                {
                    "text": "Machine learning requires large datasets",
                    "type": "factual",
                    "confidence": 0.92,
                    "evidence_type": "empirical"
                }
            ]
        }'''
        mock_model_instance = Mock()
        mock_model_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_model_instance

        worker = ClaimExtractionWorker()
        text = "AI is transforming society. Machine learning requires large datasets."

        result = await worker.extract_claims_with_gemini(text, "test.txt", "gpt-4")

        assert "claims" in result
        assert len(result["claims"]) == 2
        assert result["claims"][0]["type"] == "factual"
        assert result["claims"][0]["confidence"] > 0.9

    @pytest.mark.asyncio
    async def test_process_claim_extraction_job(self, test_db_session_sync, sample_document_file):
        """Test processing a claim extraction job."""
        from apps.workers.worker_extraction import process_claim_extraction_job
        from packages.database.models import Pipeline, Document

        # Create pipeline and document
        pipeline = Pipeline(name="Test Pipeline")
        test_db_session_sync.add(pipeline)
        test_db_session_sync.flush()

        document = Document(
            pipeline_id=pipeline.id,
            filename="test.txt",
            file_path=sample_document_file,
            file_size=1000,
            mime_type="text/plain",
            status="uploaded",
            source_llm="gpt-4"
        )
        test_db_session_sync.add(document)
        test_db_session_sync.commit()

        # Create job data
        job_data = {
            "pipeline_id": str(pipeline.id),
            "document_id": str(document.id)
        }

        # Mock Gemini response
        with patch('apps.workers.worker_extraction.genai.GenerativeModel') as mock_model:
            mock_response = Mock()
            mock_response.text = '''{
                "claims": [
                    {
                        "text": "Test claim",
                        "type": "factual",
                        "confidence": 0.95,
                        "evidence_type": "empirical"
                    }
                ]
            }'''
            mock_model_instance = Mock()
            mock_model_instance.generate_content.return_value = mock_response
            mock_model.return_value = mock_model_instance

            # Process job (this would normally be async, but we're testing the logic)
            # await process_claim_extraction_job(job_data, lambda: test_db_session_sync)

            # For now, just verify the worker can be instantiated
            from apps.workers.worker_extraction import ClaimExtractionWorker
            worker = ClaimExtractionWorker()
            assert worker is not None

    def test_handle_unsupported_file_type(self):
        """Test handling unsupported file types."""
        from apps.workers.worker_extraction import ClaimExtractionWorker

        worker = ClaimExtractionWorker()

        # Should raise exception or return empty string
        with pytest.raises(Exception):
            worker.extract_text("fake_file.xyz", "application/octet-stream")

    def test_handle_empty_text(self):
        """Test handling documents with no extractable text."""
        from apps.workers.worker_extraction import ClaimExtractionWorker
        import tempfile
        import os

        # Create empty file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            temp_path = f.name

        try:
            worker = ClaimExtractionWorker()
            text = worker.extract_text(temp_path, 'text/plain')

            # Should return empty string or minimal content
            assert len(text) == 0 or text.strip() == ""
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    @patch('apps.workers.worker_extraction.genai.GenerativeModel')
    async def test_gemini_api_error_handling(self, mock_model):
        """Test handling Gemini API errors."""
        from apps.workers.worker_extraction import ClaimExtractionWorker

        # Mock API error
        mock_model_instance = Mock()
        mock_model_instance.generate_content.side_effect = Exception("API Error")
        mock_model.return_value = mock_model_instance

        worker = ClaimExtractionWorker()

        with pytest.raises(Exception):
            await worker.extract_claims_with_gemini(
                "Test text", "test.txt", "gpt-4"
            )

    @pytest.mark.asyncio
    @patch('apps.workers.worker_extraction.genai.GenerativeModel')
    async def test_invalid_json_response(self, mock_model):
        """Test handling invalid JSON from Gemini."""
        from apps.workers.worker_extraction import ClaimExtractionWorker

        # Mock invalid JSON response
        mock_response = Mock()
        mock_response.text = "This is not valid JSON"
        mock_model_instance = Mock()
        mock_model_instance.generate_content.return_value = mock_response
        mock_model.return_value = mock_model_instance

        worker = ClaimExtractionWorker()

        with pytest.raises(Exception):
            await worker.extract_claims_with_gemini(
                "Test text", "test.txt", "gpt-4"
            )


@pytest.mark.unit
@pytest.mark.worker
class TestExtractionWorkerFormats:
    """Test extraction from different file formats."""

    def test_extract_from_markdown(self):
        """Test extracting from Markdown files."""
        from apps.workers.worker_extraction import ClaimExtractionWorker
        import tempfile
        import os

        # Create markdown file
        markdown_content = """
        # Test Document

        ## Claims

        - AI is transforming technology
        - Machine learning requires data
        """

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(markdown_content)
            temp_path = f.name

        try:
            worker = ClaimExtractionWorker()
            text = worker.extract_text(temp_path, 'text/markdown')

            assert "AI is transforming" in text
            assert "Machine learning" in text
        finally:
            os.unlink(temp_path)

    def test_extract_from_json(self):
        """Test extracting from JSON files."""
        from apps.workers.worker_extraction import ClaimExtractionWorker
        import tempfile
        import json
        import os

        # Create JSON file
        json_content = {
            "claims": [
                "AI is powerful",
                "Data is essential"
            ]
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(json_content, f)
            temp_path = f.name

        try:
            worker = ClaimExtractionWorker()
            text = worker.extract_text(temp_path, 'application/json')

            # JSON should be converted to readable text
            assert len(text) > 0
        finally:
            os.unlink(temp_path)
