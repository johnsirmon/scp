#!/usr/bin/env python3
"""
Quick demo of the SCP system functionality.
"""

import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scp.core import SCPManager
from scp.models import Priority, Status


def demo_scp():
    """Demonstrate basic SCP functionality."""
    print("🚀 SCP (Support Context Protocol) Demo")
    print("=" * 40)
    
    # Initialize SCP (without vector search for this demo)
    print("\n1. Initializing SCP...")
    scp = SCPManager(data_dir="./demo_data", use_vector_search=False)
    print(f"   ✅ SCP initialized (vector search: {scp.vector_search_enabled})")
    
    # Add a case manually
    print("\n2. Adding a case manually...")
    case_data = {
        "case_id": "DEMO-001",
        "title": "Database connection timeout",
        "priority": Priority.HIGH,
        "status": Status.OPEN,
        "customer": "Demo Customer",
        "description": "Database connection timeouts are occurring",
        "symptoms": ["Connection refused", "30 second timeout"],
        "error_messages": ["SqlException: Timeout expired"]
    }
    
    case1 = scp.add_case(case_data)
    print(f"   ✅ Added: {case1.case_id} - {case1.title}")
    
    # Parse ICM text
    print("\n3. Parsing ICM text...")
    icm_text = """
    ICM-789: API Gateway 503 errors
    Priority: Critical
    Customer: Test Corp
    
    Symptoms:
    • Service unavailable
    • High latency
    
    Error: HTTP 503 Service Unavailable
    """
    
    case2 = scp.add_case(icm_text)
    print(f"   ✅ Parsed: {case2.case_id} - {case2.title}")
    
    # Retrieve a case
    print("\n4. Retrieving case...")
    retrieved = scp.get_case("DEMO-001")
    if retrieved:
        print(f"   ✅ Found: {retrieved.case_id}")
        print(f"      Title: {retrieved.title}")
        print(f"      Status: {retrieved.status.value}")
        print(f"      Symptoms: {len(retrieved.symptoms)} found")
    
    # Search cases
    print("\n5. Searching cases...")
    results = scp.search_cases("database")
    print(f"   ✅ Found {len(results)} cases matching 'database'")
    for result in results:
        print(f"      • {result.case.case_id}: {result.case.title}")
    
    # Get statistics
    print("\n6. System statistics...")
    stats = scp.get_stats()
    print(f"   Total cases: {stats.total_cases}")
    print(f"   Memory usage: {stats.memory_usage_mb:.2f} MB")
    print(f"   Open cases: {stats.cases_by_status.get(Status.OPEN, 0)}")
    
    # Export data
    print("\n7. Exporting data...")
    json_data = scp.export_data()
    print(f"   ✅ Exported {len(json_data)} characters of JSON data")
    
    print("\n🎉 Demo completed successfully!")
    print("\nSCP system is working correctly. Key features demonstrated:")
    print("  ✅ Case creation and storage")
    print("  ✅ ICM text parsing")
    print("  ✅ Case retrieval and search")
    print("  ✅ Statistics and data export")
    print("  ✅ Memory-based storage")
    
    print("\nNext steps:")
    print("  • Try the CLI: python -m scp --help")
    print("  • Start the API: python -m scp api")
    print("  • Run the full example: python example.py")


if __name__ == "__main__":
    try:
        demo_scp()
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
