"""
Unit tests for Pipeline API endpoints.
Tests CRUD operations, document uploads, and pipeline execution.
"""

import pytest
from uuid import uuid4
from fastapi import status


@pytest.mark.unit
@pytest.mark.api
class TestPipelineEndpoints:
    """Test pipeline API endpoints."""

    def test_create_pipeline(self, test_client, sample_pipeline_data):
        """Test creating a new pipeline."""
        response = test_client.post("/api/v1/pipelines/", json=sample_pipeline_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "id" in data
        assert data["name"] == sample_pipeline_data["name"]
        assert data["status"] == "pending"
        assert data["total_claims"] == 0
        assert data["total_dependencies"] == 0
        assert data["total_contradictions"] == 0

    def test_create_pipeline_without_name(self, test_client):
        """Test creating pipeline without name."""
        response = test_client.post("/api/v1/pipelines/", json={})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "id" in data
        assert data["name"] is None or data["name"] == ""

    def test_get_pipeline(self, test_client, sample_pipeline_data):
        """Test retrieving a pipeline by ID."""
        # Create pipeline
        create_response = test_client.post("/api/v1/pipelines/", json=sample_pipeline_data)
        pipeline_id = create_response.json()["id"]

        # Get pipeline
        response = test_client.get(f"/api/v1/pipelines/{pipeline_id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == pipeline_id
        assert data["name"] == sample_pipeline_data["name"]

    def test_get_nonexistent_pipeline(self, test_client):
        """Test retrieving a non-existent pipeline."""
        fake_id = str(uuid4())
        response = test_client.get(f"/api/v1/pipelines/{fake_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_list_pipelines(self, test_client, sample_pipeline_data):
        """Test listing all pipelines."""
        # Create multiple pipelines
        for i in range(3):
            data = sample_pipeline_data.copy()
            data["name"] = f"Pipeline {i}"
            test_client.post("/api/v1/pipelines/", json=data)

        # List pipelines
        response = test_client.get("/api/v1/pipelines/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 3

    def test_list_pipelines_with_pagination(self, test_client, sample_pipeline_data):
        """Test listing pipelines with pagination."""
        # Create multiple pipelines
        for i in range(5):
            data = sample_pipeline_data.copy()
            data["name"] = f"Pipeline {i}"
            test_client.post("/api/v1/pipelines/", json=data)

        # List with limit
        response = test_client.get("/api/v1/pipelines/?limit=2&offset=0")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) <= 2

    def test_list_pipelines_with_status_filter(self, test_client, sample_pipeline_data):
        """Test listing pipelines filtered by status."""
        # Create pipeline
        test_client.post("/api/v1/pipelines/", json=sample_pipeline_data)

        # List pending pipelines
        response = test_client.get("/api/v1/pipelines/?status=pending")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        for pipeline in data:
            assert pipeline["status"] == "pending"

    def test_update_pipeline(self, test_client, sample_pipeline_data):
        """Test updating a pipeline."""
        # Create pipeline
        create_response = test_client.post("/api/v1/pipelines/", json=sample_pipeline_data)
        pipeline_id = create_response.json()["id"]

        # Update pipeline
        update_data = {"name": "Updated Pipeline Name"}
        response = test_client.patch(f"/api/v1/pipelines/{pipeline_id}", json=update_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Pipeline Name"

    def test_delete_pipeline(self, test_client, sample_pipeline_data):
        """Test deleting a pipeline."""
        # Create pipeline
        create_response = test_client.post("/api/v1/pipelines/", json=sample_pipeline_data)
        pipeline_id = create_response.json()["id"]

        # Delete pipeline
        response = test_client.delete(f"/api/v1/pipelines/{pipeline_id}")

        assert response.status_code == status.HTTP_200_OK

        # Verify deletion
        get_response = test_client.get(f"/api/v1/pipelines/{pipeline_id}")
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_upload_documents(self, test_client, sample_pipeline_data, sample_document_file):
        """Test uploading documents to a pipeline."""
        # Create pipeline
        create_response = test_client.post("/api/v1/pipelines/", json=sample_pipeline_data)
        pipeline_id = create_response.json()["id"]

        # Upload document
        with open(sample_document_file, 'rb') as f:
            files = {'files': ('test.txt', f, 'text/plain')}
            data = {'source_llm': 'gpt-4'}
            response = test_client.post(
                f"/api/v1/pipelines/{pipeline_id}/documents",
                files=files,
                data=data
            )

        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert len(result["documents"]) == 1
        assert result["documents"][0]["filename"] == "test.txt"
        assert result["documents"][0]["status"] == "uploaded"

    def test_upload_multiple_documents(self, test_client, sample_pipeline_data, sample_document_file):
        """Test uploading multiple documents."""
        # Create pipeline
        create_response = test_client.post("/api/v1/pipelines/", json=sample_pipeline_data)
        pipeline_id = create_response.json()["id"]

        # Upload multiple documents
        with open(sample_document_file, 'rb') as f1:
            with open(sample_document_file, 'rb') as f2:
                files = [
                    ('files', ('test1.txt', f1, 'text/plain')),
                    ('files', ('test2.txt', f2, 'text/plain'))
                ]
                response = test_client.post(
                    f"/api/v1/pipelines/{pipeline_id}/documents",
                    files=files
                )

        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert len(result["documents"]) == 2

    def test_upload_unsupported_file_type(self, test_client, sample_pipeline_data):
        """Test uploading unsupported file type."""
        # Create pipeline
        create_response = test_client.post("/api/v1/pipelines/", json=sample_pipeline_data)
        pipeline_id = create_response.json()["id"]

        # Try to upload unsupported file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xyz', delete=False) as f:
            f.write("test content")
            temp_path = f.name

        try:
            with open(temp_path, 'rb') as f:
                files = {'files': ('test.xyz', f, 'application/octet-stream')}
                response = test_client.post(
                    f"/api/v1/pipelines/{pipeline_id}/documents",
                    files=files
                )

            assert response.status_code == status.HTTP_400_BAD_REQUEST
        finally:
            import os
            os.unlink(temp_path)

    def test_start_pipeline(self, test_client, sample_pipeline_data, sample_document_file):
        """Test starting a pipeline."""
        # Create pipeline and upload document
        create_response = test_client.post("/api/v1/pipelines/", json=sample_pipeline_data)
        pipeline_id = create_response.json()["id"]

        with open(sample_document_file, 'rb') as f:
            files = {'files': ('test.txt', f, 'text/plain')}
            test_client.post(
                f"/api/v1/pipelines/{pipeline_id}/documents",
                files=files
            )

        # Start pipeline
        response = test_client.post(f"/api/v1/pipelines/{pipeline_id}/start")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "job_ids" in data
        assert len(data["job_ids"]) > 0

    def test_start_pipeline_without_documents(self, test_client, sample_pipeline_data):
        """Test starting pipeline without documents."""
        # Create pipeline without documents
        create_response = test_client.post("/api/v1/pipelines/", json=sample_pipeline_data)
        pipeline_id = create_response.json()["id"]

        # Try to start pipeline
        response = test_client.post(f"/api/v1/pipelines/{pipeline_id}/start")

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.unit
@pytest.mark.api
class TestPipelineValidation:
    """Test pipeline validation and error handling."""

    def test_create_pipeline_with_invalid_metadata(self, test_client):
        """Test creating pipeline with invalid metadata."""
        invalid_data = {
            "name": "Test",
            "metadata": "not a dict"  # Should be dict
        }

        response = test_client.post("/api/v1/pipelines/", json=invalid_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_pipeline_with_invalid_uuid(self, test_client):
        """Test getting pipeline with invalid UUID format."""
        response = test_client.get("/api/v1/pipelines/not-a-uuid")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_update_pipeline_with_invalid_data(self, test_client, sample_pipeline_data):
        """Test updating pipeline with invalid data."""
        # Create pipeline
        create_response = test_client.post("/api/v1/pipelines/", json=sample_pipeline_data)
        pipeline_id = create_response.json()["id"]

        # Try to update with invalid data
        invalid_update = {"status": "invalid_status"}
        response = test_client.patch(f"/api/v1/pipelines/{pipeline_id}", json=invalid_update)

        # Should either reject or ignore invalid fields
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_422_UNPROCESSABLE_ENTITY]
