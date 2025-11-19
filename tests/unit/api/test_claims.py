"""
Unit tests for Claims API endpoints.
Tests claim retrieval, filtering, and statistics.
"""

import pytest
from uuid import uuid4
from fastapi import status


@pytest.mark.unit
@pytest.mark.api
class TestClaimsEndpoints:
    """Test claims API endpoints."""

    @pytest.mark.asyncio
    async def test_get_claims_for_pipeline(self, async_test_client, test_db_session, sample_pipeline_data, sample_claim_data):
        """Test retrieving claims for a specific pipeline."""
        # Create pipeline
        from packages.database.models import Pipeline, Claim

        pipeline = Pipeline(**sample_pipeline_data)
        test_db_session.add(pipeline)
        await test_db_session.flush()

        # Create claims
        for i in range(3):
            claim_data = sample_claim_data.copy()
            claim_data["text"] = f"Test claim {i}"
            claim_data["pipeline_id"] = pipeline.id
            claim_data["document_id"] = uuid4()
            claim = Claim(**claim_data)
            test_db_session.add(claim)

        await test_db_session.commit()

        # Get claims
        response = await async_test_client.get(
            f"/api/v1/claims/?pipeline_id={pipeline.id}"
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 3

    @pytest.mark.asyncio
    async def test_get_claim_by_id(self, async_test_client, test_db_session, sample_pipeline_data, sample_claim_data):
        """Test retrieving a specific claim."""
        from packages.database.models import Pipeline, Claim

        # Create pipeline and claim
        pipeline = Pipeline(**sample_pipeline_data)
        test_db_session.add(pipeline)
        await test_db_session.flush()

        claim_data = sample_claim_data.copy()
        claim_data["pipeline_id"] = pipeline.id
        claim_data["document_id"] = uuid4()
        claim = Claim(**claim_data)
        test_db_session.add(claim)
        await test_db_session.commit()

        # Get claim
        response = await async_test_client.get(f"/api/v1/claims/{claim.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(claim.id)
        assert data["text"] == claim_data["text"]

    @pytest.mark.asyncio
    async def test_get_claims_with_pagination(self, async_test_client, test_db_session, sample_pipeline_data, sample_claim_data):
        """Test claims pagination."""
        from packages.database.models import Pipeline, Claim

        # Create pipeline
        pipeline = Pipeline(**sample_pipeline_data)
        test_db_session.add(pipeline)
        await test_db_session.flush()

        # Create many claims
        for i in range(25):
            claim_data = sample_claim_data.copy()
            claim_data["text"] = f"Claim {i}"
            claim_data["pipeline_id"] = pipeline.id
            claim_data["document_id"] = uuid4()
            claim = Claim(**claim_data)
            test_db_session.add(claim)

        await test_db_session.commit()

        # Get first page
        response = await async_test_client.get(
            f"/api/v1/claims/?pipeline_id={pipeline.id}&limit=10&offset=0"
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 10

        # Get second page
        response = await async_test_client.get(
            f"/api/v1/claims/?pipeline_id={pipeline.id}&limit=10&offset=10"
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 10

    @pytest.mark.asyncio
    async def test_filter_claims_by_type(self, async_test_client, test_db_session, sample_pipeline_data, sample_claim_data):
        """Test filtering claims by type."""
        from packages.database.models import Pipeline, Claim

        # Create pipeline
        pipeline = Pipeline(**sample_pipeline_data)
        test_db_session.add(pipeline)
        await test_db_session.flush()

        # Create claims of different types
        types = ["factual", "statistical", "causal", "opinion", "hypothesis"]
        for claim_type in types:
            for i in range(2):
                claim_data = sample_claim_data.copy()
                claim_data["text"] = f"{claim_type} claim {i}"
                claim_data["claim_type"] = claim_type
                claim_data["pipeline_id"] = pipeline.id
                claim_data["document_id"] = uuid4()
                claim = Claim(**claim_data)
                test_db_session.add(claim)

        await test_db_session.commit()

        # Filter by type
        response = await async_test_client.get(
            f"/api/v1/claims/?pipeline_id={pipeline.id}&claim_type=factual"
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        for claim in data:
            assert claim["claim_type"] == "factual"

    @pytest.mark.asyncio
    async def test_get_claim_dependencies(self, async_test_client, test_db_session, sample_pipeline_data, sample_claim_data, sample_dependency_data):
        """Test getting dependencies for a claim."""
        from packages.database.models import Pipeline, Claim, Dependency

        # Create pipeline
        pipeline = Pipeline(**sample_pipeline_data)
        test_db_session.add(pipeline)
        await test_db_session.flush()

        # Create claims
        claim1_data = sample_claim_data.copy()
        claim1_data["pipeline_id"] = pipeline.id
        claim1_data["document_id"] = uuid4()
        claim1 = Claim(**claim1_data)
        test_db_session.add(claim1)

        claim2_data = sample_claim_data.copy()
        claim2_data["pipeline_id"] = pipeline.id
        claim2_data["document_id"] = uuid4()
        claim2 = Claim(**claim2_data)
        test_db_session.add(claim2)

        await test_db_session.flush()

        # Create dependency
        dep_data = sample_dependency_data.copy()
        dep_data["pipeline_id"] = pipeline.id
        dep_data["source_claim_id"] = claim1.id
        dep_data["target_claim_id"] = claim2.id
        dependency = Dependency(**dep_data)
        test_db_session.add(dependency)
        await test_db_session.commit()

        # Get dependencies for claim1
        response = await async_test_client.get(f"/api/v1/claims/{claim1.id}/dependencies")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) > 0

    @pytest.mark.asyncio
    async def test_get_claim_stats(self, async_test_client, test_db_session, sample_pipeline_data, sample_claim_data):
        """Test getting claim statistics for a pipeline."""
        from packages.database.models import Pipeline, Claim

        # Create pipeline
        pipeline = Pipeline(**sample_pipeline_data)
        test_db_session.add(pipeline)
        await test_db_session.flush()

        # Create claims with different types
        types_count = {"factual": 5, "statistical": 3, "causal": 2}
        for claim_type, count in types_count.items():
            for i in range(count):
                claim_data = sample_claim_data.copy()
                claim_data["claim_type"] = claim_type
                claim_data["pipeline_id"] = pipeline.id
                claim_data["document_id"] = uuid4()
                claim = Claim(**claim_data)
                test_db_session.add(claim)

        await test_db_session.commit()

        # Get stats
        response = await async_test_client.get(
            f"/api/v1/claims/pipeline/{pipeline.id}/stats"
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_claims"] == 10
        assert data["by_type"]["factual"] == 5
        assert data["by_type"]["statistical"] == 3
        assert data["by_type"]["causal"] == 2

    @pytest.mark.asyncio
    async def test_get_foundational_claims(self, async_test_client, test_db_session, sample_pipeline_data, sample_claim_data):
        """Test filtering for foundational claims."""
        from packages.database.models import Pipeline, Claim

        # Create pipeline
        pipeline = Pipeline(**sample_pipeline_data)
        test_db_session.add(pipeline)
        await test_db_session.flush()

        # Create foundational and regular claims
        for i in range(3):
            claim_data = sample_claim_data.copy()
            claim_data["pipeline_id"] = pipeline.id
            claim_data["document_id"] = uuid4()
            claim_data["is_foundational"] = True
            claim = Claim(**claim_data)
            test_db_session.add(claim)

        for i in range(5):
            claim_data = sample_claim_data.copy()
            claim_data["pipeline_id"] = pipeline.id
            claim_data["document_id"] = uuid4()
            claim_data["is_foundational"] = False
            claim = Claim(**claim_data)
            test_db_session.add(claim)

        await test_db_session.commit()

        # Get all claims and count foundational
        response = await async_test_client.get(
            f"/api/v1/claims/?pipeline_id={pipeline.id}"
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        foundational_count = sum(1 for claim in data if claim["is_foundational"])
        assert foundational_count == 3

    @pytest.mark.asyncio
    async def test_get_nonexistent_claim(self, async_test_client):
        """Test getting a non-existent claim."""
        fake_id = str(uuid4())
        response = await async_test_client.get(f"/api/v1/claims/{fake_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.unit
@pytest.mark.api
class TestClaimsValidation:
    """Test claims validation and error handling."""

    @pytest.mark.asyncio
    async def test_get_claims_with_invalid_uuid(self, async_test_client):
        """Test getting claim with invalid UUID."""
        response = await async_test_client.get("/api/v1/claims/not-a-uuid")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_get_claims_with_invalid_filter(self, async_test_client):
        """Test getting claims with invalid filter."""
        response = await async_test_client.get(
            "/api/v1/claims/?claim_type=invalid_type"
        )

        # Should either return empty or reject invalid filter
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_422_UNPROCESSABLE_ENTITY]
