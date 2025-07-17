"""
Data models for the Support Context Protocol (SCP) system.
Defines structured case data and related entities.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator


class Priority(str, Enum):
    """Case priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Status(str, Enum):
    """Case status values."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PENDING_CUSTOMER = "pending_customer"
    PENDING_MICROSOFT = "pending_microsoft"
    RESOLVED = "resolved"
    CLOSED = "closed"


class EscalationFlag(str, Enum):
    """EPS escalation flags."""
    EPS_CRITICAL = "eps_critical"
    EPS_HIGH = "eps_high"
    BRANDON_FLAG = "brandon_flag"
    CUSTOMER_ESCALATION = "customer_escalation"
    MEDIA_ATTENTION = "media_attention"


class CaseTag(BaseModel):
    """Represents a case tag with confidence score."""
    name: str = Field(..., description="Tag name")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    source: str = Field(..., description="Source of the tag (auto, manual, etc.)")


class LogEntry(BaseModel):
    """Represents a log entry or finding."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    content: str = Field(..., description="Log content")
    source: Optional[str] = Field(None, description="Log source (LAW, DCR, etc.)")
    level: Optional[str] = Field(None, description="Log level (error, warning, info)")
    
    
class CaseMetrics(BaseModel):
    """Case metrics and analytics."""
    response_time_hours: Optional[float] = None
    resolution_time_hours: Optional[float] = None
    customer_satisfaction: Optional[float] = Field(None, ge=1.0, le=5.0)
    engineering_effort_hours: Optional[float] = None
    escalation_count: int = Field(default=0)


class SupportCase(BaseModel):
    """Main support case data model."""
    
    # Core identifiers
    case_id: str = Field(..., description="Unique case identifier (ICM ID)")
    title: str = Field(..., description="Case title/summary")
    
    # Case details
    customer: Optional[str] = Field(None, description="Customer name or ID")
    product: Optional[str] = Field(None, description="Product or service affected")
    component: Optional[str] = Field(None, description="Specific component/feature")
    
    # Status and priority
    status: Status = Field(default=Status.OPEN)
    priority: Priority = Field(default=Priority.MEDIUM)
    severity: Optional[str] = Field(None, description="Severity level")
    
    # Temporal data
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    due_date: Optional[datetime] = None
    
    # Technical details
    symptoms: List[str] = Field(default_factory=list, description="Observed symptoms")
    error_messages: List[str] = Field(default_factory=list, description="Error messages")
    reproduction_steps: List[str] = Field(default_factory=list, description="Steps to reproduce")
    
    # Analysis and findings
    root_cause: Optional[str] = Field(None, description="Identified root cause")
    solution: Optional[str] = Field(None, description="Applied solution")
    workaround: Optional[str] = Field(None, description="Temporary workaround")
    
    # Logs and external data
    logs: List[LogEntry] = Field(default_factory=list, description="Log entries")
    law_uri: Optional[str] = Field(None, description="Log Analytics Workspace URI")
    dcr_uri: Optional[str] = Field(None, description="Data Collection Rule URI")
    
    # Classification and tagging
    tags: List[CaseTag] = Field(default_factory=list, description="Case tags")
    category: Optional[str] = Field(None, description="Primary category")
    subcategory: Optional[str] = Field(None, description="Sub-category")
    
    # Escalations and flags
    escalation_flags: List[EscalationFlag] = Field(default_factory=list)
    brandon_flags: List[str] = Field(default_factory=list, description="Brandon-specific flags")
    
    # Relationships
    related_cases: List[str] = Field(default_factory=list, description="Related case IDs")
    parent_case: Optional[str] = Field(None, description="Parent case ID if this is a sub-case")
    
    # Free-form fields
    description: str = Field(default="", description="Detailed case description")
    rendered_description: Optional[str] = Field(None, description="HTML/formatted description")
    notes: List[str] = Field(default_factory=list, description="Internal notes")
    
    # Metrics and analytics
    metrics: CaseMetrics = Field(default_factory=CaseMetrics)
    
    # Custom fields for integration
    custom_fields: Dict[str, Any] = Field(default_factory=dict, description="Custom integration fields")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @validator('updated_at', pre=True, always=True)
    def set_updated_at(cls, v):
        """Automatically update the updated_at timestamp."""
        return datetime.utcnow()
    
    def add_tag(self, name: str, confidence: float = 1.0, source: str = "manual") -> None:
        """Add a tag to the case."""
        # Remove existing tag with same name
        self.tags = [tag for tag in self.tags if tag.name != name]
        # Add new tag
        self.tags.append(CaseTag(name=name, confidence=confidence, source=source))
    
    def add_log(self, content: str, source: Optional[str] = None, level: Optional[str] = None) -> None:
        """Add a log entry to the case."""
        self.logs.append(LogEntry(content=content, source=source, level=level))
    
    def add_escalation_flag(self, flag: EscalationFlag) -> None:
        """Add an escalation flag if not already present."""
        if flag not in self.escalation_flags:
            self.escalation_flags.append(flag)
    
    def get_text_content(self) -> str:
        """Get all text content for vector search indexing."""
        content_parts = [
            self.title,
            self.description,
            " ".join(self.symptoms),
            " ".join(self.error_messages),
            " ".join(self.reproduction_steps),
            " ".join(self.notes),
        ]
        
        if self.root_cause:
            content_parts.append(self.root_cause)
        if self.solution:
            content_parts.append(self.solution)
        if self.workaround:
            content_parts.append(self.workaround)
        
        # Add log content
        content_parts.extend([log.content for log in self.logs])
        
        # Add tag names
        content_parts.extend([tag.name for tag in self.tags])
        
        return " ".join(filter(None, content_parts))


class CaseQuery(BaseModel):
    """Model for case search queries."""
    query: str = Field(..., description="Search query text")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum results to return")
    case_ids: Optional[List[str]] = Field(None, description="Specific case IDs to search within")
    status_filter: Optional[List[Status]] = Field(None, description="Filter by status")
    priority_filter: Optional[List[Priority]] = Field(None, description="Filter by priority")
    date_from: Optional[datetime] = Field(None, description="Filter cases from this date")
    date_to: Optional[datetime] = Field(None, description="Filter cases to this date")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")


class CaseUpdate(BaseModel):
    """Model for partial case updates."""
    title: Optional[str] = None
    status: Optional[Status] = None
    priority: Optional[Priority] = None
    description: Optional[str] = None
    solution: Optional[str] = None
    workaround: Optional[str] = None
    root_cause: Optional[str] = None
    
    # Lists that can be appended to
    symptoms: Optional[List[str]] = None
    error_messages: Optional[List[str]] = None
    reproduction_steps: Optional[List[str]] = None
    notes: Optional[List[str]] = None
    
    class Config:
        """Allow partial updates."""
        extra = "forbid"


class SearchResult(BaseModel):
    """Model for search results."""
    case: SupportCase
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Similarity score")
    matched_fields: List[str] = Field(default_factory=list, description="Fields that matched the query")


class SCPStats(BaseModel):
    """Statistics about the SCP system."""
    total_cases: int
    cases_by_status: Dict[Status, int]
    cases_by_priority: Dict[Priority, int]
    avg_resolution_time_hours: Optional[float]
    top_tags: List[Dict[str, Union[str, int]]]
    memory_usage_mb: float
