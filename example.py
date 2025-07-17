#!/usr/bin/env python3
"""
Example usage script for the SCP (Support Context Protocol) system.
Demonstrates key features and usage patterns.
"""

import json
from datetime import datetime, timedelta
from scp.core import SCPManager
from scp.models import Priority, Status, CaseTag


def main():
    """Run example SCP usage scenarios."""
    print("🚀 SCP (Support Context Protocol) Example Usage")
    print("=" * 50)
    
    # Initialize SCP
    print("\n1. Initializing SCP Manager...")
    scp = SCPManager(data_dir="./example_data")
    print(f"   Vector search enabled: {scp.vector_search_enabled}")
    
    # Example 1: Add a case manually
    print("\n2. Adding a case manually...")
    case_data = {
        "case_id": "ICM-123456",
        "title": "Database connection timeout in production",
        "priority": Priority.HIGH,
        "status": Status.OPEN,
        "customer": "Contoso Corp",
        "product": "Azure SQL Database",
        "description": "Users experiencing connection timeouts when accessing the main database.",
        "symptoms": [
            "Connection refused errors",
            "Timeout after 30 seconds",
            "Intermittent connectivity issues"
        ],
        "error_messages": [
            "System.Data.SqlClient.SqlException: Timeout expired",
            "Connection failed: The operation has timed out"
        ]
    }
    
    case1 = scp.add_case(case_data)
    print(f"   ✅ Added case: {case1.case_id} - {case1.title}")
    
    # Example 2: Parse ICM text
    print("\n3. Parsing ICM text...")
    icm_text = """
    ICM-789012: API Gateway returning 503 errors
    Priority: Critical
    Customer: Fabrikam Inc
    Product: Azure API Management
    
    Symptoms:
    • Service unavailable errors
    • High latency on requests
    • Multiple customer complaints
    
    Error: HTTP 503 Service Unavailable
    Started: 2024-01-15 14:30:00
    """
    
    case2 = scp.add_case(icm_text)
    print(f"   ✅ Parsed and added case: {case2.case_id} - {case2.title}")
    print(f"   Auto-detected tags: {[tag.name for tag in case2.tags]}")
    
    # Example 3: Add logs to a case
    print("\n4. Adding logs to a case...")
    log_content = """
    2024-01-15 14:30:15 ERROR [ConnectionPool] Failed to acquire connection from pool
    2024-01-15 14:30:16 WARN [DatabaseManager] Connection timeout exceeded (30s)
    2024-01-15 14:30:17 ERROR [ApiController] Database query failed: timeout
    """
    
    success = scp.add_case_logs(case1.case_id, log_content, source="ApplicationLogs")
    if success:
        print(f"   ✅ Added logs to case {case1.case_id}")
    
    # Example 4: Search for cases
    print("\n5. Searching for cases...")
    search_results = scp.search_cases("database timeout connection")
    print(f"   Found {len(search_results)} matching cases:")
    for i, result in enumerate(search_results[:3], 1):
        score_text = f" (score: {result.similarity_score:.3f})" if scp.vector_search_enabled else ""
        print(f"   {i}. {result.case.case_id} - {result.case.title[:50]}...{score_text}")
    
    # Example 5: Find similar cases
    print("\n6. Finding similar cases...")
    similar_cases = scp.find_similar_cases(case1.case_id, limit=3)
    print(f"   Found {len(similar_cases)} similar cases to {case1.case_id}:")
    for i, result in enumerate(similar_cases, 1):
        print(f"   {i}. {result.case.case_id} - {result.case.title[:40]}... (score: {result.similarity_score:.3f})")
    
    # Example 6: Update a case
    print("\n7. Updating a case...")
    from scp.models import CaseUpdate
    updates = CaseUpdate(
        status=Status.IN_PROGRESS,
        solution="Increased connection pool size and timeout values",
        notes=["Applied temporary fix", "Monitoring for improvements"]
    )
    
    updated_case = scp.update_case(case1.case_id, updates)
    if updated_case:
        print(f"   ✅ Updated case {case1.case_id} status to {updated_case.status.value}")
    
    # Example 7: Get case context for LLM
    print("\n8. Getting case context for LLM...")
    context = scp.get_case_context(case1.case_id)
    if context:
        print(f"   📋 Case context summary:")
        print(f"      Total logs: {context['summary']['total_logs']}")
        print(f"      Tags: {context['summary']['tag_count']}")
        print(f"      Days open: {context['summary']['days_open']}")
        print(f"      Similar cases: {len(context['similar_cases'])}")
    
    # Example 8: Bulk operations
    print("\n9. Bulk tag updates...")
    tag_mappings = {
        case1.case_id: ["performance", "database", "critical-fix"],
        case2.case_id: ["api", "availability", "customer-impact"]
    }
    
    updated_count = scp.bulk_update_tags(tag_mappings)
    print(f"   ✅ Updated tags for {updated_count} cases")
    
    # Example 9: System statistics
    print("\n10. System statistics...")
    stats = scp.get_stats()
    print(f"    Total cases: {stats.total_cases}")
    print(f"    Memory usage: {stats.memory_usage_mb:.2f} MB")
    print(f"    Cases by status:")
    for status, count in stats.cases_by_status.items():
        if count > 0:
            print(f"      {status.value}: {count}")
    
    if stats.top_tags:
        print(f"    Top tags:")
        for tag_info in stats.top_tags[:3]:
            print(f"      {tag_info['name']}: {tag_info['count']} cases")
    
    # Example 10: Export and import
    print("\n11. Data export/import...")
    
    # Export data
    export_file = "./example_export.json"
    json_data = scp.export_data(export_file)
    print(f"    ✅ Exported data to {export_file}")
    
    # Create a new SCP instance and import
    scp2 = SCPManager(data_dir="./example_data_2")
    imported_count = scp2.import_data(json_data)
    print(f"    ✅ Imported {imported_count} cases to new SCP instance")
    
    # Example 11: Advanced querying
    print("\n12. Advanced querying...")
    from scp.models import CaseQuery
    
    advanced_query = CaseQuery(
        query="API service error",
        limit=5,
        status_filter=[Status.OPEN, Status.IN_PROGRESS],
        priority_filter=[Priority.HIGH, Priority.CRITICAL]
    )
    
    results = scp.search_cases(advanced_query)
    print(f"    Advanced query returned {len(results)} results")
    
    # Save all data
    print("\n13. Saving all data...")
    scp.save_all()
    print("    ✅ All data saved to disk")
    
    print("\n🎉 Example completed successfully!")
    print("\nNext steps:")
    print("  • Try the CLI: python -m scp")
    print("  • Start the API: python -m scp api")
    print("  • Explore the interactive mode: python -m scp interactive")


if __name__ == "__main__":
    main()
