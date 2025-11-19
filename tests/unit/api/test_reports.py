"""
Unit tests for Reports API endpoints.
Tests report generation, retrieval, and contradiction detection.
"""

import pytest
from uuid import uuid4
from fastapi import status


@pytest.mark.unit
@pytest.mark.api
class TestReportsEndpoints:
    """Test reports API endpoints."""

    @pytest.mark.asyncio
    async def test_analyze_dependencies(self, async_test_client, test_db_session, sample_pipeline_data):
        """Test starting dependency analysis."""
        from packages.database.models import Pipeline

        # Create pipeline
        pipeline = Pipeline(**sample_pipeline_data)
        test_db_session.add(pipeline)
        await test_db_session.commit()

        # Start dependency analysis
        response = await async_test_client.post(
            f"/api/v1/reports/{pipeline.id}/analyze-dependencies"
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "job_id" in data
        assert "message" in data

    @pytest.mark.asyncio
    async def test_detect_contradictions(self, async_test_client, test_db_session, sample_pipeline_data):
        """Test detecting contradictions."""
        from packages.database.models import Pipeline

        # Create pipeline
        pipeline = Pipeline(**sample_pipeline_data)
        test_db_session.add(pipeline)
        await test_db_session.commit()

        # Detect contradictions
        response = await async_test_client.post(
            f"/api/v1/reports/{pipeline.id}/detect-contradictions"
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list) or "contradictions" in data

    @pytest.mark.asyncio
    async def test_generate_report(self, async_test_client, test_db_session, sample_pipeline_data):
        """Test generating a synthesis report."""
        from packages.database.models import Pipeline

        # Create pipeline
        pipeline = Pipeline(**sample_pipeline_data)
        test_db_session.add(pipeline)
        await test_db_session.commit()

        # Generate report
        response = await async_test_client.post(
            f"/api/v1/reports/{pipeline.id}/generate?report_type=synthesis"
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "job_id" in data or "report_id" in data

    @pytest.mark.asyncio
    async def test_get_reports_for_pipeline(self, async_test_client, test_db_session, sample_pipeline_data):
        """Test retrieving reports for a pipeline."""
        from packages.database.models import Pipeline, Report

        # Create pipeline
        pipeline = Pipeline(**sample_pipeline_data)
        test_db_session.add(pipeline)
        await test_db_session.flush()

        # Create reports
        for i in range(2):
            report = Report(
                pipeline_id=pipeline.id,
                report_type="synthesis",
                title=f"Test Report {i}",
                content=f"# Report {i}\n\nTest content",
                content_html=f"<h1>Report {i}</h1><p>Test content</p>",
                summary=f"Summary of report {i}"
            )
            test_db_session.add(report)

        await test_db_session.commit()

        # Get reports
        response = await async_test_client.get(f"/api/v1/reports/{pipeline.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 2

    @pytest.mark.asyncio
    async def test_get_latest_report(self, async_test_client, test_db_session, sample_pipeline_data):
        """Test retrieving the latest report."""
        from packages.database.models import Pipeline, Report
        import asyncio

        # Create pipeline
        pipeline = Pipeline(**sample_pipeline_data)
        test_db_session.add(pipeline)
        await test_db_session.flush()

        # Create reports with delay to ensure different timestamps
        for i in range(3):
            report = Report(
                pipeline_id=pipeline.id,
                report_type="synthesis",
                title=f"Report {i}",
                content=f"Content {i}",
                content_html=f"<p>Content {i}</p>",
                summary=f"Summary {i}"
            )
            test_db_session.add(report)
            await test_db_session.flush()
            if i < 2:
                await asyncio.sleep(0.1)

        await test_db_session.commit()

        # Get latest report
        response = await async_test_client.get(
            f"/api/v1/reports/{pipeline.id}/latest"
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "Report 2" in data["title"]

    @pytest.mark.asyncio
    async def test_get_specific_report(self, async_test_client, test_db_session, sample_pipeline_data):
        """Test retrieving a specific report by ID."""
        from packages.database.models import Pipeline, Report

        # Create pipeline
        pipeline = Pipeline(**sample_pipeline_data)
        test_db_session.add(pipeline)
        await test_db_session.flush()

        # Create report
        report = Report(
            pipeline_id=pipeline.id,
            report_type="synthesis",
            title="Specific Report",
            content="# Specific Content",
            content_html="<h1>Specific Content</h1>",
            summary="Specific summary"
        )
        test_db_session.add(report)
        await test_db_session.commit()

        # Get specific report
        response = await async_test_client.get(
            f"/api/v1/reports/report/{report.id}"
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Specific Report"

    @pytest.mark.asyncio
    async def test_get_contradictions(self, async_test_client, test_db_session, sample_pipeline_data):
        """Test retrieving contradictions for a pipeline."""
        from packages.database.models import Pipeline, Claim, Contradiction

        # Create pipeline
        pipeline = Pipeline(**sample_pipeline_data)
        test_db_session.add(pipeline)
        await test_db_session.flush()

        # Create claims
        claim1 = Claim(
            pipeline_id=pipeline.id,
            document_id=uuid4(),
            text="AI is always beneficial",
            claim_type="opinion",
            confidence=0.8,
            is_foundational=False
        )
        claim2 = Claim(
            pipeline_id=pipeline.id,
            document_id=uuid4(),
            text="AI has potential risks",
            claim_type="opinion",
            confidence=0.85,
            is_foundational=False
        )
        test_db_session.add(claim1)
        test_db_session.add(claim2)
        await test_db_session.flush()

        # Create contradiction
        contradiction = Contradiction(
            pipeline_id=pipeline.id,
            claim_a_id=claim1.id,
            claim_b_id=claim2.id,
            contradiction_type="direct",
            severity="high",
            explanation="These claims directly contradict each other",
            confidence=0.92,
            resolution_suggestion="Consider context and scope"
        )
        test_db_session.add(contradiction)
        await test_db_session.commit()

        # Get contradictions
        response = await async_test_client.get(
            f"/api/v1/reports/{pipeline.id}/contradictions"
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1
        assert data[0]["contradiction_type"] == "direct"
        assert data[0]["severity"] == "high"

    @pytest.mark.asyncio
    async def test_get_reports_empty_pipeline(self, async_test_client, test_db_session, sample_pipeline_data):
        """Test getting reports for pipeline with no reports."""
        from packages.database.models import Pipeline

        # Create pipeline without reports
        pipeline = Pipeline(**sample_pipeline_data)
        test_db_session.add(pipeline)
        await test_db_session.commit()

        # Get reports
        response = await async_test_client.get(f"/api/v1/reports/{pipeline.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 0

    @pytest.mark.asyncio
    async def test_get_nonexistent_report(self, async_test_client):
        """Test getting a non-existent report."""
        fake_id = str(uuid4())
        response = await async_test_client.get(f"/api/v1/reports/report/{fake_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.unit
@pytest.mark.api
class TestReportsValidation:
    """Test reports validation and error handling."""

    @pytest.mark.asyncio
    async def test_analyze_dependencies_invalid_pipeline(self, async_test_client):
        """Test dependency analysis with invalid pipeline ID."""
        fake_id = str(uuid4())
        response = await async_test_client.post(
            f"/api/v1/reports/{fake_id}/analyze-dependencies"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_generate_report_invalid_type(self, async_test_client, test_db_session, sample_pipeline_data):
        """Test generating report with invalid type."""
        from packages.database.models import Pipeline

        # Create pipeline
        pipeline = Pipeline(**sample_pipeline_data)
        test_db_session.add(pipeline)
        await test_db_session.commit()

        # Try to generate report with invalid type
        response = await async_test_client.post(
            f"/api/v1/reports/{pipeline.id}/generate?report_type=invalid_type"
        )

        # Should either reject or default to valid type
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY
        ]
