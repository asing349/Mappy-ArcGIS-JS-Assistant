"""
Tests for Module 1: Corpus Loader + Schema Validation
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.simple_corpus_loader import CorpusLoader, DocumentPage, DocumentCorpus, LoadingStats


class TestCorpusLoader:
    """Test suite for corpus loader functionality."""
    
    @pytest.fixture
    def sample_document_data(self):
        """Sample document data for testing."""
        return {
            "id": "test_doc_1",
            "type": "api_reference",
            "title": "Map Class - ArcGIS Maps SDK for JavaScript 4.33",
            "url": "https://developers.arcgis.com/javascript/latest/api-reference/esri-Map.html",
            "content": "The Map class contains properties and methods for creating and working with web maps. A map is composed of a basemap and operational layers.",
            "metadata": {
                "section_count": 3,
                "last_modified": "2025-08-31"
            }
        }
    
    @pytest.fixture
    def sample_corpus_data(self):
        """Sample corpus data for testing."""
        return {
            "total_pages": 3,
            "api_reference_pages": 2,
            "guide_pages": 1,
            "sample_pages": 0,
            "scrape_date": "2025-08-31 22:13:32",
            "documents": [
                {
                    "id": "doc_1",
                    "type": "api_reference",
                    "title": "Map Class",
                    "url": "https://example.com/map",
                    "content": "Map class documentation content here."
                },
                {
                    "id": "doc_2", 
                    "type": "api_reference",
                    "title": "MapView Class",
                    "url": "https://example.com/mapview",
                    "content": "MapView class documentation content here."
                },
                {
                    "id": "doc_3",
                    "type": "guide",
                    "title": "Getting Started Guide",
                    "url": "https://example.com/guide",
                    "content": "This guide shows you how to get started with the ArcGIS Maps SDK."
                }
            ]
        }
    
    def test_document_validation_valid(self, sample_document_data):
        """Test valid document passes validation."""
        doc = DocumentPage(**sample_document_data)
        
        assert doc.id == "test_doc_1"
        assert doc.type == "api_reference"
        assert doc.title == "Map Class - ArcGIS Maps SDK for JavaScript 4.33"
        assert len(doc.content) > 10
    
    def test_document_validation_invalid_type(self, sample_document_data):
        """Test invalid document type fails validation."""
        sample_document_data["type"] = "invalid_type"
        
        with pytest.raises(ValueError):
            DocumentPage(**sample_document_data)
    
    def test_document_validation_empty_content(self, sample_document_data):
        """Test empty content fails validation."""
        sample_document_data["content"] = ""
        
        with pytest.raises(ValueError):
            DocumentPage(**sample_document_data)
    
    def test_document_validation_invalid_url(self, sample_document_data):
        """Test invalid URL fails validation."""
        sample_document_data["url"] = "not_a_url"
        
        with pytest.raises(ValueError):
            DocumentPage(**sample_document_data)
    
    def test_version_detection(self):
        """Test SDK version detection from URL and content."""
        loader = CorpusLoader()
        
        # Test URL version detection
        doc1 = {"url": "https://developers.arcgis.com/javascript/latest/api-reference/esri-Map.html"}
        assert loader.detect_version(doc1) == "4.33"
        
        doc2 = {"url": "https://developers.arcgis.com/javascript/4.33/api-reference/esri-Map.html"}
        assert loader.detect_version(doc2) == "4.33"
        
        # Test content version detection  
        doc3 = {"url": "", "content": "This feature was added in version 4.33."}
        assert loader.detect_version(doc3) == "4.33"
        
        # Test no version found
        doc4 = {"url": "", "content": "No version info here."}
        assert loader.detect_version(doc4) is None
    
    def test_duplicate_url_detection(self, sample_document_data):
        """Test duplicate URL detection."""
        loader = CorpusLoader()
        
        # First document should validate fine
        doc1 = loader.validate_document(sample_document_data, 0)
        assert doc1 is not None
        
        # Second document with same URL should trigger warning
        doc2 = loader.validate_document(sample_document_data, 1)
        assert doc2 is not None
        assert any("Duplicate URL" in error for error in loader.stats.errors)
    
    def test_loading_stats_tracking(self):
        """Test loading statistics tracking."""
        loader = CorpusLoader()
        
        # Initial stats
        assert loader.stats.files_processed == 0
        assert loader.stats.total_documents == 0
        assert loader.stats.api_docs == 0
        
        # Simulate processing documents
        sample_doc = {
            "id": "test",
            "type": "api_reference", 
            "title": "Test Doc",
            "url": "https://test.com",
            "content": "Test content here."
        }
        
        doc = loader.validate_document(sample_doc, 0)
        
        assert doc is not None
        assert loader.stats.api_docs == 1
        assert loader.stats.total_documents == 0  # Only incremented in load_single_file
    
    def test_json_loading_with_temp_file(self, sample_corpus_data):
        """Test JSON loading with temporary file."""
        loader = CorpusLoader()
        
        # Create temporary JSON file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_corpus_data, f)
            temp_path = Path(f.name)
        
        try:
            # Test loading
            data = loader.load_json_streaming(temp_path)
            
            assert data is not None
            assert data["total_pages"] == 3
            assert len(data["documents"]) == 3
            
        finally:
            # Clean up
            temp_path.unlink()
    
    def test_corpus_validation(self, sample_corpus_data):
        """Test full corpus validation."""
        corpus = DocumentCorpus(**sample_corpus_data)
        
        assert corpus.total_pages == 3
        assert len(corpus.documents) == 3
        assert corpus.api_reference_pages == 2
    
    def test_corpus_validation_mismatch(self, sample_corpus_data):
        """Test corpus validation with mismatched counts."""
        # Make total_pages not match document count
        sample_corpus_data["total_pages"] = 5
        
        with pytest.raises(ValueError, match="Document count"):
            DocumentCorpus(**sample_corpus_data)
    
    @patch('psutil.Process')
    def test_memory_monitoring(self, mock_process):
        """Test memory usage monitoring."""
        # Mock memory info
        mock_process.return_value.memory_info.return_value.rss = 100 * 1024 * 1024  # 100MB
        
        loader = CorpusLoader()
        loader.print_loading_stats()
        
        # Should not raise any errors
        assert True
    
    def test_document_type_counting(self):
        """Test document type counter updates.""" 
        loader = CorpusLoader()
        
        # Test different document types
        api_doc = {
            "id": "api1",
            "type": "api_reference",
            "title": "API Doc",
            "url": "https://test.com/api",
            "content": "API documentation content"
        }
        
        guide_doc = {
            "id": "guide1", 
            "type": "guide",
            "title": "Guide Doc",
            "url": "https://test.com/guide",
            "content": "Guide documentation content"
        }
        
        sample_doc = {
            "id": "sample1",
            "type": "sample",
            "title": "Sample Doc", 
            "url": "https://test.com/sample",
            "content": "Sample documentation content"
        }
        
        loader.validate_document(api_doc, 0)
        loader.validate_document(guide_doc, 1)
        loader.validate_document(sample_doc, 2)
        
        assert loader.stats.api_docs == 1
        assert loader.stats.guide_docs == 1
        assert loader.stats.sample_docs == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])