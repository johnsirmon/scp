"""
Test suite for the SCP (Support Context Protocol) system.
Basic tests to verify functionality.
"""

import tempfile
import shutil

from scp.core import SCPManager
from scp.models import SupportCase, Priority, Status
from scp.parsers import ICMParser


class TestSCPCore:
    """Test the core SCP functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.scp = SCPManager(data_dir=self.temp_dir, use_vector_search=False)
    
    def teardown_method(self):
        """Cleanup test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_add_case_dict(self):
        """Test adding a case from dictionary."""
        case_data = {
            "case_id": "TEST-001",
            "title": "Test Case",
            "priority": Priority.HIGH,
            "status": Status.OPEN,
            "description": "Test description"
        }
        
        case = self.scp.add_case(case_data)
        assert case.case_id == "TEST-001"
        assert case.title == "Test Case"
        assert case.priority == Priority.HIGH
        assert case.status == Status.OPEN
    
    def test_get_case(self):
        """Test retrieving a case."""
        case_data = {
            "case_id": "TEST-002",
            "title": "Another Test Case"
        }
        
        # Add case
        self.scp.add_case(case_data)
        
        # Retrieve case
        retrieved_case = self.scp.get_case("TEST-002")
        assert retrieved_case is not None
        assert retrieved_case.case_id == "TEST-002"
        assert retrieved_case.title == "Another Test Case"
    
    def test_update_case(self):
        """Test updating a case."""
        # Add case
        case_data = {"case_id": "TEST-003", "title": "Update Test"}
        self.scp.add_case(case_data)
        
        # Update case
        from scp.models import CaseUpdate
        updates = CaseUpdate(
            status=Status.IN_PROGRESS,
            solution="Test solution"
        )
        
        updated_case = self.scp.update_case("TEST-003", updates)
        assert updated_case is not None
        assert updated_case.status == Status.IN_PROGRESS
        assert updated_case.solution == "Test solution"
    
    def test_delete_case(self):
        """Test deleting a case."""
        # Add case
        case_data = {"case_id": "TEST-004", "title": "Delete Test"}
        self.scp.add_case(case_data)
        
        # Verify case exists
        assert self.scp.get_case("TEST-004") is not None
        
        # Delete case
        deleted = self.scp.delete_case("TEST-004")
        assert deleted is True
        
        # Verify case no longer exists
        assert self.scp.get_case("TEST-004") is None
    
    def test_search_cases(self):
        """Test case searching."""
        # Add test cases
        cases = [
            {"case_id": "SEARCH-001", "title": "Database connection issue"},
            {"case_id": "SEARCH-002", "title": "API timeout problem"},
            {"case_id": "SEARCH-003", "title": "Network connectivity failure"}
        ]
        
        for case_data in cases:
            self.scp.add_case(case_data)
        
        # Search for database-related cases
        results = self.scp.search_cases("database")
        assert len(results) >= 1
        assert any("database" in result.case.title.lower() for result in results)
        
        # Search for connection-related cases
        results = self.scp.search_cases("connection")
        assert len(results) >= 2  # Should match both database and network cases


class TestICMParser:
    """Test the ICM parser functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.parser = ICMParser()
    
    def test_parse_icm_text_basic(self):
        """Test basic ICM text parsing."""
        icm_text = """
        ICM-123456: Database connection timeout
        Priority: High
        Status: Open
        Customer: Test Corp
        Product: Azure SQL
        
        The database is experiencing connection timeouts.
        Users are unable to access the application.
        """
        
        case = self.parser.parse_icm_text(icm_text)
        assert case.case_id == "123456"  # ICM prefix removed
        assert "Database connection timeout" in case.title
        assert case.priority == Priority.HIGH
        assert case.status == Status.OPEN
        assert case.customer == "Test Corp"
        assert case.product == "Azure SQL"
    
    def test_extract_symptoms(self):
        """Test symptom extraction."""
        text = """
        Issues observed:
        • Connection refused errors
        • Timeout after 30 seconds  
        • Users cannot login
        """
        
        symptoms = self.parser._extract_symptoms(text)
        assert len(symptoms) == 3
        assert "Connection refused errors" in symptoms
        assert "Timeout after 30 seconds" in symptoms
        assert "Users cannot login" in symptoms
    
    def test_extract_error_messages(self):
        """Test error message extraction."""
        text = """
        Error: System.Data.SqlClient.SqlException: Timeout expired
        Exception: Connection failed
        Failed: Unable to connect to database
        """
        
        errors = self.parser._extract_error_messages(text)
        assert len(errors) >= 1
        assert any("timeout" in error.lower() for error in errors)
    
    def test_auto_tagging(self):
        """Test automatic tag generation."""
        text = """
        Database connection timeout issue.
        Performance is slow and users are experiencing latency.
        Authentication errors are also occurring.
        """
        
        tags = self.parser._generate_tags(text)
        tag_names = [tag.name for tag in tags]
        
        assert "database" in tag_names
        assert "performance" in tag_names
        assert "authentication" in tag_names


class TestMemoryStore:
    """Test the memory store functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
        from scp.memory import MemoryStore
        self.store = MemoryStore(data_dir=self.temp_dir)
    
    def teardown_method(self):
        """Cleanup test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_add_and_get_case(self):
        """Test adding and retrieving cases."""
        case = SupportCase(
            case_id="MEMORY-001",
            title="Memory Store Test"
        )
        
        # Add case
        self.store.add_case(case)
        
        # Retrieve case
        retrieved = self.store.get_case("MEMORY-001")
        assert retrieved is not None
        assert retrieved.case_id == "MEMORY-001"
        assert retrieved.title == "Memory Store Test"
    
    def test_case_count(self):
        """Test case counting."""
        initial_count = self.store.get_case_count()
        
        # Add cases
        for i in range(5):
            case = SupportCase(
                case_id=f"COUNT-{i:03d}",
                title=f"Count Test {i}"
            )
            self.store.add_case(case)
        
        final_count = self.store.get_case_count()
        assert final_count == initial_count + 5
    
    def test_export_import(self):
        """Test data export and import."""
        # Add test cases
        cases = [
            SupportCase(case_id="EXPORT-001", title="Export Test 1"),
            SupportCase(case_id="EXPORT-002", title="Export Test 2")
        ]
        
        for case in cases:
            self.store.add_case(case)
        
        # Export data
        json_data = self.store.export_to_json()
        assert "EXPORT-001" in json_data
        assert "EXPORT-002" in json_data
        
        # Clear store and import
        self.store.clear_all()
        assert self.store.get_case_count() == 0
        
        imported_count = self.store.import_from_json(json_data)
        assert imported_count == 2
        assert self.store.get_case_count() == 2


def run_tests():
    """Run all tests."""
    print("🧪 Running SCP Tests...")
    
    # Run tests using pytest
    test_files = [
        "test_scp_core",
        "test_icm_parser", 
        "test_memory_store"
    ]
    
    try:
        # Simple test runner without pytest dependency
        test_core = TestSCPCore()
        test_parser = TestICMParser()
        test_memory = TestMemoryStore()
        
        # Run core tests
        print("Testing SCP Core...")
        test_core.setup_method()
        test_core.test_add_case_dict()
        test_core.test_get_case()
        test_core.test_update_case()
        test_core.test_delete_case()
        test_core.test_search_cases()
        test_core.teardown_method()
        print("✅ Core tests passed")
        
        # Run parser tests
        print("Testing ICM Parser...")
        test_parser.setup_method()
        test_parser.test_parse_icm_text_basic()
        test_parser.test_extract_symptoms()
        test_parser.test_extract_error_messages()
        test_parser.test_auto_tagging()
        print("✅ Parser tests passed")
        
        # Run memory tests
        print("Testing Memory Store...")
        test_memory.setup_method()
        test_memory.test_add_and_get_case()
        test_memory.test_case_count()
        test_memory.test_export_import()
        test_memory.teardown_method()
        print("✅ Memory store tests passed")
        
        print("\n🎉 All tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    run_tests()
