import aiofiles
import os
from pathlib import Path
from typing import List, Dict
import mimetypes
import hashlib
from datetime import datetime
from fastapi import UploadFile, HTTPException
import logging
from uuid import uuid4

logger = logging.getLogger(__name__)

class UploadHandler:
    def __init__(self, base_path: str = "/mnt/uploads"):
        self.base_path = Path(base_path)
        self.supported_types = {
            'application/pdf': ['.pdf'],
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
            'text/markdown': ['.md'],
            'text/plain': ['.txt'],
            'application/json': ['.json']
        }
        self.max_size = 100 * 1024 * 1024  # 100MB

    async def save_upload(
        self,
        file: UploadFile,
        pipeline_id: str,
        user_id: str
    ) -> Dict[str, any]:
        """Save uploaded file and return metadata"""

        # Validate file
        await self._validate_file(file)

        # Create directory structure
        upload_dir = self.base_path / user_id / pipeline_id
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename
        file_ext = Path(file.filename).suffix
        unique_name = f"{uuid4()}{file_ext}"
        file_path = upload_dir / unique_name

        # Calculate hash while saving
        hasher = hashlib.sha256()
        file_size = 0

        try:
            async with aiofiles.open(file_path, 'wb') as f:
                while chunk := await file.read(8192):
                    await f.write(chunk)
                    hasher.update(chunk)
                    file_size += len(chunk)

            logger.info(f"Saved file: {file_path} ({file_size} bytes)")

            return {
                'filename': file.filename,
                'stored_name': unique_name,
                'file_path': str(file_path),
                'file_size': file_size,
                'mime_type': file.content_type,
                'sha256': hasher.hexdigest(),
                'uploaded_at': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"File save error: {e}")
            # Cleanup on error
            if file_path.exists():
                file_path.unlink()
            raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    async def _validate_file(self, file: UploadFile):
        """Validate uploaded file"""

        # Check mime type
        if file.content_type not in self.supported_types:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file.content_type}"
            )

        # Check file extension
        file_ext = Path(file.filename).suffix.lower()
        allowed_exts = self.supported_types[file.content_type]
        if file_ext not in allowed_exts:
            raise HTTPException(
                status_code=400,
                detail=f"File extension {file_ext} doesn't match content type"
            )

        # Check file size (read first chunk to verify)
        first_chunk = await file.read(self.max_size + 1)
        await file.seek(0)  # Reset file pointer

        if len(first_chunk) > self.max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Max size: {self.max_size / 1024 / 1024}MB"
            )

    async def save_multiple(
        self,
        files: List[UploadFile],
        pipeline_id: str,
        user_id: str
    ) -> List[Dict[str, any]]:
        """Save multiple files"""
        results = []

        for file in files:
            try:
                metadata = await self.save_upload(file, pipeline_id, user_id)
                results.append(metadata)
            except Exception as e:
                logger.error(f"Failed to save {file.filename}: {e}")
                results.append({
                    'filename': file.filename,
                    'error': str(e)
                })

        return results

    def get_file_path(self, user_id: str, pipeline_id: str, filename: str) -> Path:
        """Get full path to uploaded file"""
        return self.base_path / user_id / pipeline_id / filename

    async def delete_pipeline_files(self, user_id: str, pipeline_id: str):
        """Delete all files for a pipeline"""
        pipeline_dir = self.base_path / user_id / pipeline_id

        if pipeline_dir.exists():
            import shutil
            shutil.rmtree(pipeline_dir)
            logger.info(f"Deleted pipeline files: {pipeline_dir}")

upload_handler = UploadHandler()
