"""
FastAPI REST API for the SCP system.
Provides HTTP endpoints for case management and search operations.
"""

from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from .core import SCPManager
from .models import (
    SupportCase, CaseQuery, CaseUpdate, SearchResult, 
    SCPStats, Priority, Status
)

# Initialize FastAPI app
app = FastAPI(
    title="Support Context Protocol (SCP) API",
    description="Intelligent case triage and context management system",
    version="0.1.0"
)

# Global SCP manager instance
scp_manager: Optional[SCPManager] = None


@app.on_event("startup")
async def startup_event():
    """Initialize SCP manager on startup."""
    global scp_manager
    scp_manager = SCPManager()


@app.on_event("shutdown")
async def shutdown_event():
    """Save data on shutdown."""
    if scp_manager:
        scp_manager.save_all()


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


# Case management endpoints
@app.post("/cases", response_model=SupportCase)
async def create_case(case_data: Dict[str, Any] = Body(...)):
    """
    Create a new support case.
    
    Args:
        case_data: Case data as JSON object
        
    Returns:
        Created SupportCase object
    """
    if not scp_manager:
        raise HTTPException(status_code=500, detail="SCP manager not initialized")
    
    try:
        case = scp_manager.add_case(case_data)
        return case
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating case: {str(e)}")


@app.post("/cases/parse")
async def parse_case_text(
    text: str = Body(..., description="Raw case text to parse"),
    case_id: Optional[str] = Body(None, description="Optional explicit case ID")
):
    """
    Parse case text and create a new case.
    
    Args:
        text: Raw case text (ICM summary, etc.)
        case_id: Optional explicit case ID
        
    Returns:
        Parsed and created SupportCase object
    """
    if not scp_manager:
        raise HTTPException(status_code=500, detail="SCP manager not initialized")
    
    try:
        # Parse the text
        if case_id:
            case = scp_manager.icm_parser.parse_icm_text(text, case_id)
        else:
            case = scp_manager.icm_parser.parse_icm_text(text)
        
        # Add to SCP
        case = scp_manager.add_case(case)
        return case
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parsing case: {str(e)}")


@app.get("/cases/{case_id}", response_model=SupportCase)
async def get_case(case_id: str):
    """
    Get a specific case by ID.
    
    Args:
        case_id: Case identifier
        
    Returns:
        SupportCase object
    """
    if not scp_manager:
        raise HTTPException(status_code=500, detail="SCP manager not initialized")
    
    case = scp_manager.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
    
    return case


@app.put("/cases/{case_id}", response_model=SupportCase)
async def update_case(case_id: str, updates: CaseUpdate):
    """
    Update an existing case.
    
    Args:
        case_id: Case identifier
        updates: Updates to apply
        
    Returns:
        Updated SupportCase object
    """
    if not scp_manager:
        raise HTTPException(status_code=500, detail="SCP manager not initialized")
    
    case = scp_manager.update_case(case_id, updates)
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
    
    return case


@app.delete("/cases/{case_id}")
async def delete_case(case_id: str):
    """
    Delete a case.
    
    Args:
        case_id: Case identifier
        
    Returns:
        Success message
    """
    if not scp_manager:
        raise HTTPException(status_code=500, detail="SCP manager not initialized")
    
    deleted = scp_manager.delete_case(case_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
    
    return {"message": f"Case {case_id} deleted successfully"}


@app.get("/cases", response_model=List[SupportCase])
async def list_cases(
    limit: int = Query(50, le=1000, description="Maximum number of cases to return"),
    status: Optional[Status] = Query(None, description="Filter by status"),
    priority: Optional[Priority] = Query(None, description="Filter by priority")
):
    """
    List all cases with optional filtering.
    
    Args:
        limit: Maximum number of cases to return
        status: Optional status filter
        priority: Optional priority filter
        
    Returns:
        List of SupportCase objects
    """
    if not scp_manager:
        raise HTTPException(status_code=500, detail="SCP manager not initialized")
    
    # Get all cases
    all_cases = scp_manager.memory.get_all_cases()
    
    # Apply filters
    filtered_cases = all_cases
    if status:
        filtered_cases = [case for case in filtered_cases if case.status == status]
    if priority:
        filtered_cases = [case for case in filtered_cases if case.priority == priority]
    
    # Sort by updated_at descending and apply limit
    filtered_cases.sort(key=lambda x: x.updated_at, reverse=True)
    return filtered_cases[:limit]


# Search endpoints
@app.post("/search", response_model=List[SearchResult])
async def search_cases(query: CaseQuery):
    """
    Search for cases using text query and filters.
    
    Args:
        query: Search query object
        
    Returns:
        List of SearchResult objects
    """
    if not scp_manager:
        raise HTTPException(status_code=500, detail="SCP manager not initialized")
    
    try:
        results = scp_manager.search_cases(query)
        return results
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Search error: {str(e)}")


@app.get("/cases/{case_id}/similar", response_model=List[SearchResult])
async def find_similar_cases(
    case_id: str,
    limit: int = Query(5, le=50, description="Maximum number of similar cases"),
    threshold: float = Query(0.1, ge=0.0, le=1.0, description="Similarity threshold")
):
    """
    Find cases similar to the given case.
    
    Args:
        case_id: Case identifier
        limit: Maximum number of results
        threshold: Minimum similarity threshold
        
    Returns:
        List of SearchResult objects
    """
    if not scp_manager:
        raise HTTPException(status_code=500, detail="SCP manager not initialized")
    
    # Check if case exists
    if not scp_manager.get_case(case_id):
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
    
    try:
        results = scp_manager.find_similar_cases(case_id, limit=limit, threshold=threshold)
        return results
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error finding similar cases: {str(e)}")


# Context and analytics endpoints
@app.get("/cases/{case_id}/context")
async def get_case_context(case_id: str):
    """
    Get structured context for a case suitable for LLM injection.
    
    Args:
        case_id: Case identifier
        
    Returns:
        Structured case context
    """
    if not scp_manager:
        raise HTTPException(status_code=500, detail="SCP manager not initialized")
    
    context = scp_manager.get_case_context(case_id)
    if not context:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
    
    return context


@app.post("/cases/{case_id}/logs")
async def add_case_logs(
    case_id: str,
    log_content: str = Body(..., description="Raw log content"),
    source: str = Body("api", description="Log source identifier"),
    log_format: str = Body("text", description="Log format (text or json)")
):
    """
    Add log entries to a case.
    
    Args:
        case_id: Case identifier
        log_content: Raw log content
        source: Log source identifier
        log_format: Format of logs ("text" or "json")
        
    Returns:
        Success message
    """
    if not scp_manager:
        raise HTTPException(status_code=500, detail="SCP manager not initialized")
    
    success = scp_manager.add_case_logs(case_id, log_content, source, log_format)
    if not success:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found or log parsing failed")
    
    return {"message": f"Logs added to case {case_id}"}


@app.get("/stats", response_model=SCPStats)
async def get_stats():
    """
    Get SCP system statistics.
    
    Returns:
        SCPStats object with system metrics
    """
    if not scp_manager:
        raise HTTPException(status_code=500, detail="SCP manager not initialized")
    
    return scp_manager.get_stats()


# Data management endpoints
@app.get("/export")
async def export_data():
    """
    Export all case data as JSON.
    
    Returns:
        JSON export of all cases
    """
    if not scp_manager:
        raise HTTPException(status_code=500, detail="SCP manager not initialized")
    
    try:
        json_data = scp_manager.export_data()
        return JSONResponse(
            content=json.loads(json_data),
            headers={"Content-Disposition": "attachment; filename=scp_export.json"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export error: {str(e)}")


@app.post("/import")
async def import_data(json_data: Dict[str, Any] = Body(...)):
    """
    Import case data from JSON.
    
    Args:
        json_data: JSON data containing cases
        
    Returns:
        Import statistics
    """
    if not scp_manager:
        raise HTTPException(status_code=500, detail="SCP manager not initialized")
    
    try:
        json_str = json.dumps(json_data)
        imported_count = scp_manager.import_data(json_str)
        return {"message": f"Imported {imported_count} cases successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Import error: {str(e)}")


@app.post("/save")
async def save_all():
    """
    Save all data to disk.
    
    Returns:
        Success message
    """
    if not scp_manager:
        raise HTTPException(status_code=500, detail="SCP manager not initialized")
    
    try:
        scp_manager.save_all()
        return {"message": "All data saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Save error: {str(e)}")


# Utility endpoints
@app.get("/case-ids")
async def get_case_ids():
    """
    Get all case IDs in the system.
    
    Returns:
        List of case IDs
    """
    if not scp_manager:
        raise HTTPException(status_code=500, detail="SCP manager not initialized")
    
    return {"case_ids": scp_manager.get_case_ids()}


@app.post("/tags/bulk-update")
async def bulk_update_tags(tag_mappings: Dict[str, List[str]] = Body(...)):
    """
    Bulk update tags for multiple cases.
    
    Args:
        tag_mappings: Dict mapping case_ids to lists of tag names
        
    Returns:
        Update statistics
    """
    if not scp_manager:
        raise HTTPException(status_code=500, detail="SCP manager not initialized")
    
    try:
        updated_count = scp_manager.bulk_update_tags(tag_mappings)
        return {"message": f"Updated tags for {updated_count} cases"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Bulk update error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
