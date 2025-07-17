"""
Parsers for extracting structured data from ICM summaries and case descriptions.
Handles various input formats and extracts relevant case information.
"""

import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dateutil import parser as date_parser

from .models import SupportCase, Priority, Status, EscalationFlag, LogEntry


class ICMParser:
    """
    Parser for ICM (Incident Configuration Management) case data.
    Extracts structured information from ICM summaries and descriptions.
    """
    
    # Common patterns for parsing ICM data
    PATTERNS = {
        'case_id': [
            r'ICM[:\s-]*(\d+)',
            r'Case[:\s]+([A-Z0-9-]+)',
            r'Ticket[:\s]+([A-Z0-9-]+)',
            r'ID[:\s]+([A-Z0-9-]+)'
        ],
        'priority': [
            r'Priority[:\s]+(Critical|High|Medium|Low)',
            r'Sev[:\s]+(\d+)',
            r'Severity[:\s]+(Critical|High|Medium|Low|\d+)'
        ],
        'status': [
            r'Status[:\s]+(Open|In Progress|Pending|Resolved|Closed)',
            r'State[:\s]+(Open|In Progress|Pending|Resolved|Closed)'
        ],
        'customer': [
            r'Customer[:\s]+([^\n\r]+)',
            r'Client[:\s]+([^\n\r]+)',
            r'Organization[:\s]+([^\n\r]+)'
        ],
        'product': [
            r'Product[:\s]+([^\n\r]+)',
            r'Service[:\s]+([^\n\r]+)',
            r'Application[:\s]+([^\n\r]+)'
        ],
        'error_code': [
            r'Error[:\s]+(\d+)',
            r'Code[:\s]+([A-Z0-9_-]+)',
            r'Exception[:\s]+([A-Za-z.]+)'
        ],
        'timestamp': [
            r'(\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2})',
            r'(\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}:\d{2})',
            r'(\w+\s+\d{1,2},?\s+\d{4}\s+\d{1,2}:\d{2})'
        ]
    }
    
    # Keywords for automatic tagging
    TAG_KEYWORDS = {
        'performance': ['slow', 'timeout', 'latency', 'performance', 'delay'],
        'connectivity': ['connection', 'network', 'unreachable', 'dns'],
        'authentication': ['auth', 'login', 'permission', 'access denied'],
        'database': ['sql', 'database', 'db', 'query', 'connection pool'],
        'api': ['api', 'rest', 'endpoint', 'service', 'microservice'],
        'storage': ['storage', 'blob', 'file', 'disk', 'capacity'],
        'monitoring': ['alert', 'metric', 'dashboard', 'telemetry'],
        'security': ['security', 'vulnerability', 'breach', 'certificate']
    }
    
    # EPS escalation keywords
    EPS_KEYWORDS = {
        EscalationFlag.EPS_CRITICAL: [
            'critical', 'outage', 'down', 'service unavailable'
        ],
        EscalationFlag.EPS_HIGH: [
            'high priority', 'urgent', 'business critical'
        ],
        EscalationFlag.BRANDON_FLAG: [
            'brandon', 'escalation', 'management attention'
        ],
        EscalationFlag.CUSTOMER_ESCALATION: [
            'customer escalation', 'complaint', 'dissatisfied'
        ],
        EscalationFlag.MEDIA_ATTENTION: [
            'media', 'press', 'public', 'social media'
        ]
    }
    
    def parse_icm_text(self, text: str, case_id: Optional[str] = None) -> SupportCase:
        """
        Parse ICM text content into a SupportCase object.
        
        Args:
            text: Raw ICM text content
            case_id: Optional explicit case ID
            
        Returns:
            Parsed SupportCase object
        """
        # Extract basic fields
        extracted_case_id = case_id or self._extract_case_id(text)
        title = self._extract_title(text)
        priority = self._extract_priority(text)
        status = self._extract_status(text)
        
        # Extract additional fields
        customer = self._extract_field(text, 'customer')
        product = self._extract_field(text, 'product')
        
        # Create base case
        case = SupportCase(
            case_id=extracted_case_id or f"SCP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            title=title or "Untitled Case",
            priority=priority,
            status=status,
            customer=customer,
            product=product,
            description=text
        )
        
        # Extract symptoms and errors
        case.symptoms = self._extract_symptoms(text)
        case.error_messages = self._extract_error_messages(text)
        
        # Auto-generate tags
        case.tags = self._generate_tags(text)
        
        # Check for escalation flags
        case.escalation_flags = self._detect_escalation_flags(text)
        
        # Extract timestamps and set creation time
        timestamps = self._extract_timestamps(text)
        if timestamps:
            case.created_at = timestamps[0]
        
        return case
    
    def parse_json_data(self, data: Dict[str, Any]) -> SupportCase:
        """
        Parse case data from JSON/dictionary format.
        
        Args:
            data: Dictionary containing case data
            
        Returns:
            SupportCase object
        """
        # Direct mapping for known fields
        case_data = {}
        
        # Handle different field name variations
        field_mappings = {
            'case_id': ['case_id', 'id', 'ticket_id', 'icm_id'],
            'title': ['title', 'summary', 'subject', 'description'],
            'priority': ['priority', 'severity', 'sev'],
            'status': ['status', 'state'],
            'customer': ['customer', 'client', 'organization'],
            'product': ['product', 'service', 'application'],
            'description': ['description', 'details', 'body', 'content']
        }
        
        for field, possible_keys in field_mappings.items():
            for key in possible_keys:
                if key in data:
                    case_data[field] = data[key]
                    break
        
        # Ensure required fields
        if 'case_id' not in case_data:
            case_data['case_id'] = f"SCP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        if 'title' not in case_data:
            case_data['title'] = "Imported Case"
        
        # Handle arrays
        if 'symptoms' in data:
            case_data['symptoms'] = data['symptoms']
        if 'error_messages' in data:
            case_data['error_messages'] = data['error_messages']
        if 'tags' in data:
            # Convert simple strings to CaseTag objects if needed
            if data['tags'] and isinstance(data['tags'][0], str):
                from .models import CaseTag
                case_data['tags'] = [
                    CaseTag(name=tag, confidence=1.0, source="import")
                    for tag in data['tags']
                ]
        
        # Handle priority conversion
        if 'priority' in case_data:
            case_data['priority'] = self._normalize_priority(case_data['priority'])
        
        # Handle status conversion
        if 'status' in case_data:
            case_data['status'] = self._normalize_status(case_data['status'])
        
        return SupportCase(**case_data)
    
    def _extract_case_id(self, text: str) -> Optional[str]:
        """Extract case ID from text."""
        for pattern in self.PATTERNS['case_id']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _extract_title(self, text: str) -> Optional[str]:
        """Extract title/summary from text."""
        lines = text.strip().split('\n')
        if lines:
            # First non-empty line is likely the title
            for line in lines:
                line = line.strip()
                if line and not re.match(r'^(ICM|Case|Ticket|ID):', line, re.IGNORECASE):
                    return line[:200]  # Limit title length
        return None
    
    def _extract_priority(self, text: str) -> Priority:
        """Extract priority from text."""
        for pattern in self.PATTERNS['priority']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).lower()
                if value in ['critical', '1']:
                    return Priority.CRITICAL
                elif value in ['high', '2']:
                    return Priority.HIGH
                elif value in ['medium', '3']:
                    return Priority.MEDIUM
                elif value in ['low', '4']:
                    return Priority.LOW
        
        # Default based on keywords
        text_lower = text.lower()
        if any(word in text_lower for word in ['critical', 'outage', 'down']):
            return Priority.CRITICAL
        elif any(word in text_lower for word in ['urgent', 'high']):
            return Priority.HIGH
        else:
            return Priority.MEDIUM
    
    def _extract_status(self, text: str) -> Status:
        """Extract status from text."""
        for pattern in self.PATTERNS['status']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).lower().replace(' ', '_')
                try:
                    return Status(value)
                except ValueError:
                    pass
        return Status.OPEN
    
    def _extract_field(self, text: str, field: str) -> Optional[str]:
        """Extract a specific field from text."""
        if field in self.PATTERNS:
            for pattern in self.PATTERNS[field]:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return match.group(1).strip()
        return None
    
    def _extract_symptoms(self, text: str) -> List[str]:
        """Extract symptoms from text."""
        symptoms = []
        
        # Look for bullet points or numbered lists
        symptom_patterns = [
            r'[•\-\*]\s+([^\n\r]+)',
            r'\d+\.\s+([^\n\r]+)',
            r'Symptom[s]?[:\s]+([^\n\r]+)',
            r'Issue[s]?[:\s]+([^\n\r]+)',
            r'Problem[s]?[:\s]+([^\n\r]+)'
        ]
        
        for pattern in symptom_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            symptoms.extend([match.strip() for match in matches])
        
        return list(set(symptoms))  # Remove duplicates
    
    def _extract_error_messages(self, text: str) -> List[str]:
        """Extract error messages from text."""
        errors = []
        
        # Common error patterns
        error_patterns = [
            r'Error[:\s]+([^\n\r]+)',
            r'Exception[:\s]+([^\n\r]+)',
            r'Failed[:\s]+([^\n\r]+)',
            r'(\d{3,4}\s+\w+)',  # HTTP status codes
            r'([A-Z_]+_ERROR[:\s]+[^\n\r]+)'
        ]
        
        for pattern in error_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            errors.extend([match.strip() for match in matches if isinstance(match, str)])
        
        return list(set(errors))
    
    def _extract_timestamps(self, text: str) -> List[datetime]:
        """Extract timestamps from text."""
        timestamps = []
        
        for pattern in self.PATTERNS['timestamp']:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    timestamp = date_parser.parse(match)
                    timestamps.append(timestamp)
                except:
                    continue
        
        return sorted(timestamps)
    
    def _generate_tags(self, text: str) -> List:
        """Generate automatic tags based on content."""
        from .models import CaseTag
        
        tags = []
        text_lower = text.lower()
        
        for tag_name, keywords in self.TAG_KEYWORDS.items():
            confidence = 0.0
            matches = 0
            
            for keyword in keywords:
                if keyword in text_lower:
                    matches += 1
                    confidence += 0.2  # Each keyword adds confidence
            
            if matches > 0:
                confidence = min(confidence, 1.0)
                tags.append(CaseTag(
                    name=tag_name,
                    confidence=confidence,
                    source="auto_parser"
                ))
        
        return tags
    
    def _detect_escalation_flags(self, text: str) -> List[EscalationFlag]:
        """Detect escalation flags in text."""
        flags = []
        text_lower = text.lower()
        
        for flag, keywords in self.EPS_KEYWORDS.items():
            if any(keyword in text_lower for keyword in keywords):
                flags.append(flag)
        
        return flags
    
    def _normalize_priority(self, priority: Any) -> Priority:
        """Normalize priority value to Priority enum."""
        if isinstance(priority, Priority):
            return priority
        
        if isinstance(priority, str):
            priority_lower = priority.lower()
            if priority_lower in ['critical', 'crit', '1']:
                return Priority.CRITICAL
            elif priority_lower in ['high', '2']:
                return Priority.HIGH
            elif priority_lower in ['medium', 'med', '3']:
                return Priority.MEDIUM
            elif priority_lower in ['low', '4']:
                return Priority.LOW
        
        return Priority.MEDIUM
    
    def _normalize_status(self, status: Any) -> Status:
        """Normalize status value to Status enum."""
        if isinstance(status, Status):
            return status
        
        if isinstance(status, str):
            status_lower = status.lower().replace(' ', '_')
            try:
                return Status(status_lower)
            except ValueError:
                pass
        
        return Status.OPEN


class LogParser:
    """
    Parser for log entries and structured log data.
    Extracts relevant information from various log formats.
    """
    
    LOG_PATTERNS = {
        'timestamp': r'(\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2}(?:\.\d{3})?)',
        'level': r'\b(ERROR|WARN|WARNING|INFO|DEBUG|TRACE|FATAL)\b',
        'component': r'\[([^\]]+)\]',
        'thread': r'\(([^)]+)\)',
        'message': r'(?:ERROR|WARN|WARNING|INFO|DEBUG|TRACE|FATAL)[\s:]+(.*)'
    }
    
    def parse_log_content(self, content: str, source: str = "unknown") -> List[LogEntry]:
        """
        Parse log content into LogEntry objects.
        
        Args:
            content: Raw log content
            source: Source identifier (LAW, DCR, etc.)
            
        Returns:
            List of LogEntry objects
        """
        entries = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Extract timestamp
            timestamp = None
            timestamp_match = re.search(self.LOG_PATTERNS['timestamp'], line)
            if timestamp_match:
                try:
                    timestamp = date_parser.parse(timestamp_match.group(1))
                except:
                    timestamp = datetime.utcnow()
            else:
                timestamp = datetime.utcnow()
            
            # Extract log level
            level = None
            level_match = re.search(self.LOG_PATTERNS['level'], line)
            if level_match:
                level = level_match.group(1).lower()
            
            # Create log entry
            entry = LogEntry(
                timestamp=timestamp,
                content=line,
                source=source,
                level=level
            )
            entries.append(entry)
        
        return entries
    
    def parse_structured_logs(self, log_data: List[Dict[str, Any]], 
                            source: str = "api") -> List[LogEntry]:
        """
        Parse structured log data from API or JSON format.
        
        Args:
            log_data: List of log dictionaries
            source: Source identifier
            
        Returns:
            List of LogEntry objects
        """
        entries = []
        
        for log_item in log_data:
            # Extract timestamp
            timestamp = datetime.utcnow()
            if 'timestamp' in log_item:
                try:
                    timestamp = date_parser.parse(str(log_item['timestamp']))
                except:
                    pass
            elif '@timestamp' in log_item:
                try:
                    timestamp = date_parser.parse(str(log_item['@timestamp']))
                except:
                    pass
            
            # Extract content
            content = log_item.get('message', str(log_item))
            level = log_item.get('level', log_item.get('severity'))
            
            entry = LogEntry(
                timestamp=timestamp,
                content=content,
                source=source,
                level=level
            )
            entries.append(entry)
        
        return entries
