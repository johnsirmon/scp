"""
Command-line interface for the SCP system.
Provides interactive and direct CLI access to case management.
"""

import click
import json
import sys
from typing import Optional
from datetime import datetime

from .core import SCPManager
from .models import Priority, Status


@click.group()
@click.option('--data-dir', default='./scp_data', 
              help='Directory for SCP data storage')
@click.option('--no-vector-search', is_flag=True, 
              help='Disable vector search (use simple text search)')
@click.pass_context
def cli(ctx, data_dir: str, no_vector_search: bool):
    """Support Context Protocol (SCP) - Intelligent case triage system."""
    ctx.ensure_object(dict)
    
    # Initialize SCP manager
    ctx.obj['scp'] = SCPManager(
        data_dir=data_dir,
        use_vector_search=not no_vector_search
    )


@cli.command()
@click.option('--case-id', required=True, help='Case ID')
@click.option('--title', help='Case title/summary')
@click.option('--priority', 
              type=click.Choice(['critical', 'high', 'medium', 'low']),
              default='medium', help='Case priority')
@click.option('--status',
              type=click.Choice(['open', 'in_progress', 'pending_customer', 
                               'pending_microsoft', 'resolved', 'closed']),
              default='open', help='Case status')
@click.option('--customer', help='Customer name')
@click.option('--product', help='Product name')
@click.option('--description', help='Case description')
@click.pass_context
def add_case(ctx, case_id: str, title: Optional[str], priority: str, 
             status: str, customer: Optional[str], product: Optional[str],
             description: Optional[str]):
    """Add a new case to SCP."""
    scp: SCPManager = ctx.obj['scp']
    
    case_data = {
        'case_id': case_id,
        'title': title or f'Case {case_id}',
        'priority': Priority(priority),
        'status': Status(status),
        'description': description or ''
    }
    
    if customer:
        case_data['customer'] = customer
    if product:
        case_data['product'] = product
    
    try:
        case = scp.add_case(case_data)
        click.echo(f"✅ Added case {case.case_id}: {case.title}")
        click.echo(f"   Priority: {case.priority.value}")
        click.echo(f"   Status: {case.status.value}")
    except Exception as e:
        click.echo(f"❌ Error adding case: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--file', '-f', type=click.File('r'), 
              help='Read case data from file')
@click.option('--case-id', help='Override case ID')
@click.argument('text', required=False)
@click.pass_context
def parse_case(ctx, file, case_id: Optional[str], text: Optional[str]):
    """Parse case data from text or file."""
    scp: SCPManager = ctx.obj['scp']
    
    # Get input text
    if file:
        input_text = file.read()
    elif text:
        input_text = text
    else:
        click.echo("Reading from stdin... (Ctrl+D to finish)")
        input_text = sys.stdin.read()
    
    if not input_text.strip():
        click.echo("❌ No input provided", err=True)
        sys.exit(1)
    
    try:
        # Parse with explicit case ID if provided
        if case_id:
            case = scp.icm_parser.parse_icm_text(input_text, case_id)
        else:
            case = scp.icm_parser.parse_icm_text(input_text)
        
        # Add to SCP
        case = scp.add_case(case)
        
        click.echo(f"✅ Parsed and added case {case.case_id}")
        click.echo(f"   Title: {case.title}")
        click.echo(f"   Priority: {case.priority.value}")
        click.echo(f"   Tags: {[tag.name for tag in case.tags]}")
        
        if case.symptoms:
            click.echo(f"   Symptoms: {len(case.symptoms)} found")
        if case.error_messages:
            click.echo(f"   Errors: {len(case.error_messages)} found")
        
    except Exception as e:
        click.echo(f"❌ Error parsing case: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('case_id')
@click.pass_context
def get_case(ctx, case_id: str):
    """Get details for a specific case."""
    scp: SCPManager = ctx.obj['scp']
    
    case = scp.get_case(case_id)
    if not case:
        click.echo(f"❌ Case {case_id} not found", err=True)
        sys.exit(1)
    
    # Display case details
    click.echo(f"📋 Case {case.case_id}")
    click.echo(f"   Title: {case.title}")
    click.echo(f"   Status: {case.status.value}")
    click.echo(f"   Priority: {case.priority.value}")
    click.echo(f"   Created: {case.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    click.echo(f"   Updated: {case.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
    
    if case.customer:
        click.echo(f"   Customer: {case.customer}")
    if case.product:
        click.echo(f"   Product: {case.product}")
    
    if case.description:
        click.echo(f"   Description: {case.description[:200]}...")
    
    if case.tags:
        tags_str = ', '.join([f"{tag.name}({tag.confidence:.2f})" 
                             for tag in case.tags])
        click.echo(f"   Tags: {tags_str}")
    
    if case.escalation_flags:
        flags_str = ', '.join([flag.value for flag in case.escalation_flags])
        click.echo(f"   Escalation Flags: {flags_str}")
    
    if case.symptoms:
        click.echo(f"   Symptoms ({len(case.symptoms)}):")
        for symptom in case.symptoms[:3]:
            click.echo(f"     • {symptom}")
        if len(case.symptoms) > 3:
            click.echo(f"     ... and {len(case.symptoms) - 3} more")
    
    if case.logs:
        click.echo(f"   Logs: {len(case.logs)} entries")


@cli.command()
@click.argument('query')
@click.option('--limit', '-l', default=10, help='Maximum results')
@click.option('--status', multiple=True, 
              type=click.Choice(['open', 'in_progress', 'pending_customer',
                               'pending_microsoft', 'resolved', 'closed']),
              help='Filter by status')
@click.option('--priority', multiple=True,
              type=click.Choice(['critical', 'high', 'medium', 'low']),
              help='Filter by priority')
@click.option('--json-output', is_flag=True, help='Output as JSON')
@click.pass_context
def search(ctx, query: str, limit: int, status, priority, json_output: bool):
    """Search for cases by text query."""
    scp: SCPManager = ctx.obj['scp']
    
    # Convert filter strings to enums
    status_filter = [Status(s) for s in status] if status else None
    priority_filter = [Priority(p) for p in priority] if priority else None
    
    try:
        from .models import CaseQuery
        case_query = CaseQuery(
            query=query,
            limit=limit,
            status_filter=status_filter,
            priority_filter=priority_filter
        )
        
        results = scp.search_cases(case_query)
        
        if json_output:
            # Output as JSON
            json_results = [
                {
                    'case_id': result.case.case_id,
                    'title': result.case.title,
                    'similarity_score': result.similarity_score,
                    'status': result.case.status.value,
                    'priority': result.case.priority.value
                }
                for result in results
            ]
            click.echo(json.dumps(json_results, indent=2))
        else:
            # Human-readable output
            if not results:
                click.echo("🔍 No cases found matching the query")
                return
            
            click.echo(f"🔍 Found {len(results)} cases:")
            for i, result in enumerate(results, 1):
                case = result.case
                score_display = f"({result.similarity_score:.3f})" if scp.vector_search_enabled else ""
                click.echo(f"{i:2d}. {case.case_id} - {case.title[:60]} {score_display}")
                click.echo(f"     Status: {case.status.value}, Priority: {case.priority.value}")
                if case.tags:
                    tags_str = ', '.join([tag.name for tag in case.tags[:3]])
                    click.echo(f"     Tags: {tags_str}")
                click.echo()
    
    except Exception as e:
        click.echo(f"❌ Search error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('case_id')
@click.option('--limit', '-l', default=5, help='Maximum similar cases')
@click.pass_context
def similar(ctx, case_id: str, limit: int):
    """Find cases similar to the given case."""
    scp: SCPManager = ctx.obj['scp']
    
    # Check if case exists
    case = scp.get_case(case_id)
    if not case:
        click.echo(f"❌ Case {case_id} not found", err=True)
        sys.exit(1)
    
    try:
        results = scp.find_similar_cases(case_id, limit=limit)
        
        if not results:
            click.echo(f"🔍 No similar cases found for {case_id}")
            return
        
        click.echo(f"🔍 Cases similar to {case_id}:")
        for i, result in enumerate(results, 1):
            similar_case = result.case
            score = result.similarity_score
            click.echo(f"{i}. {similar_case.case_id} - {similar_case.title[:50]} (score: {score:.3f})")
            click.echo(f"   Status: {similar_case.status.value}, Priority: {similar_case.priority.value}")
    
    except Exception as e:
        click.echo(f"❌ Error finding similar cases: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def stats(ctx):
    """Show SCP system statistics."""
    scp: SCPManager = ctx.obj['scp']
    
    try:
        stats_data = scp.get_stats()
        
        click.echo("📊 SCP System Statistics")
        click.echo(f"   Total Cases: {stats_data.total_cases}")
        click.echo(f"   Memory Usage: {stats_data.memory_usage_mb:.2f} MB")
        
        click.echo("\n📈 Cases by Status:")
        for status, count in stats_data.cases_by_status.items():
            if count > 0:
                click.echo(f"   {status.value}: {count}")
        
        click.echo("\n🎯 Cases by Priority:")
        for priority, count in stats_data.cases_by_priority.items():
            if count > 0:
                click.echo(f"   {priority.value}: {count}")
        
        if stats_data.avg_resolution_time_hours:
            click.echo(f"\n⏱️  Average Resolution Time: {stats_data.avg_resolution_time_hours:.1f} hours")
        
        if stats_data.top_tags:
            click.echo("\n🏷️  Top Tags:")
            for tag_info in stats_data.top_tags[:5]:
                click.echo(f"   {tag_info['name']}: {tag_info['count']} cases")
        
        # Search engine stats
        if hasattr(scp.search_engine, 'get_stats'):
            search_stats = scp.search_engine.get_stats()
            if scp.vector_search_enabled:
                click.echo(f"\n🔍 Vector Search: {search_stats.get('total_vectors', 0)} vectors")
                click.echo(f"   Model: {search_stats.get('model_name', 'unknown')}")
            else:
                click.echo("\n🔍 Search: Simple text matching")
    
    except Exception as e:
        click.echo(f"❌ Error getting statistics: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--output', '-o', type=click.File('w'), 
              help='Output file (default: stdout)')
@click.pass_context
def export(ctx, output):
    """Export all case data to JSON."""
    scp: SCPManager = ctx.obj['scp']
    
    try:
        json_data = scp.export_data()
        
        if output:
            output.write(json_data)
            click.echo(f"✅ Exported data to {output.name}")
        else:
            click.echo(json_data)
    
    except Exception as e:
        click.echo(f"❌ Export error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--file', '-f', type=click.File('r'), required=True,
              help='JSON file to import')
@click.pass_context
def import_data(ctx, file):
    """Import case data from JSON file."""
    scp: SCPManager = ctx.obj['scp']
    
    try:
        json_data = file.read()
        imported_count = scp.import_data(json_data)
        click.echo(f"✅ Imported {imported_count} cases from {file.name}")
    
    except Exception as e:
        click.echo(f"❌ Import error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def interactive(ctx):
    """Start interactive SCP session."""
    scp: SCPManager = ctx.obj['scp']
    
    click.echo("🚀 Starting SCP Interactive Session")
    click.echo("   Type 'help' for commands, 'exit' to quit")
    
    while True:
        try:
            command = click.prompt("\nscp>", type=str).strip()
            
            if command.lower() in ['exit', 'quit', 'q']:
                break
            elif command.lower() in ['help', 'h']:
                click.echo("Available commands:")
                click.echo("  add <case_id> <title> - Add a new case")
                click.echo("  get <case_id> - Get case details")
                click.echo("  search <query> - Search cases")
                click.echo("  similar <case_id> - Find similar cases")
                click.echo("  stats - Show statistics")
                click.echo("  save - Save all data")
                click.echo("  help - Show this help")
                click.echo("  exit - Exit interactive mode")
            elif command.lower() == 'stats':
                ctx.invoke(stats)
            elif command.lower() == 'save':
                scp.save_all()
                click.echo("✅ All data saved")
            elif command.startswith('get '):
                case_id = command[4:].strip()
                if case_id:
                    ctx.invoke(get_case, case_id=case_id)
            elif command.startswith('search '):
                query = command[7:].strip()
                if query:
                    ctx.invoke(search, query=query, limit=5, status=(), 
                              priority=(), json_output=False)
            elif command.startswith('similar '):
                case_id = command[8:].strip()
                if case_id:
                    ctx.invoke(similar, case_id=case_id, limit=3)
            else:
                click.echo("❓ Unknown command. Type 'help' for available commands.")
        
        except KeyboardInterrupt:
            click.echo("\n👋 Goodbye!")
            break
        except Exception as e:
            click.echo(f"❌ Error: {e}")


if __name__ == '__main__':
    cli()
