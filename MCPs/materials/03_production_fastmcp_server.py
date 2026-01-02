"""
=============================================================================
PRODUCTION FASTMCP SERVER TEMPLATE
=============================================================================

A complete, production-ready MCP server with:
- Input validation (Pydantic)
- Error handling
- Logging
- Lifecycle hooks
- Resources & Prompts
- Security patterns
"""

from fastmcp import FastMCP
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Any
import asyncio
import logging
import json
import os
from datetime import datetime
from functools import wraps

# =============================================================================
# LOGGING SETUP
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MCPServer")


# =============================================================================
# CONFIGURATION
# =============================================================================

class Config:
    """Server configuration from environment."""
    
    DATA_DIR = os.getenv("DATA_DIR", "./data")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///app.db")
    API_KEY = os.getenv("API_KEY", "")
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 10 * 1024 * 1024))  # 10MB
    ALLOWED_EXTENSIONS = {".txt", ".json", ".csv", ".md"}
    RATE_LIMIT_PER_MINUTE = 100


config = Config()


# =============================================================================
# SERVER CONTEXT (STATE)
# =============================================================================

class ServerContext:
    """Shared state for the MCP server."""
    
    def __init__(self):
        self.request_count = 0
        self.start_time = None
        self.cache = {}
        self.rate_limit_tracker = {}
    
    async def initialize(self):
        """Initialize server resources."""
        self.start_time = datetime.now()
        os.makedirs(config.DATA_DIR, exist_ok=True)
        logger.info(f"Server initialized. Data dir: {config.DATA_DIR}")
    
    async def cleanup(self):
        """Cleanup server resources."""
        logger.info(f"Server shutting down. Total requests: {self.request_count}")
    
    def increment_request(self):
        self.request_count += 1
        return self.request_count
    
    def get_stats(self) -> dict:
        uptime = datetime.now() - self.start_time if self.start_time else None
        return {
            "request_count": self.request_count,
            "uptime_seconds": uptime.total_seconds() if uptime else 0,
            "cache_size": len(self.cache),
        }


ctx = ServerContext()


# =============================================================================
# CREATE MCP SERVER
# =============================================================================

mcp = FastMCP(
    name="ProductionServer",
    version="1.0.0",
)


# =============================================================================
# LIFECYCLE HOOKS
# =============================================================================

@mcp.on_startup
async def startup():
    """Called when server starts."""
    await ctx.initialize()
    logger.info("🚀 MCP Server started")


@mcp.on_shutdown
async def shutdown():
    """Called when server stops."""
    await ctx.cleanup()
    logger.info("👋 MCP Server stopped")


# =============================================================================
# DECORATORS FOR COMMON PATTERNS
# =============================================================================

def log_request(func):
    """Decorator to log tool calls."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        req_id = ctx.increment_request()
        logger.info(f"[{req_id}] {func.__name__} called with {kwargs}")
        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            logger.info(f"[{req_id}] {func.__name__} completed")
            return result
        except Exception as e:
            logger.error(f"[{req_id}] {func.__name__} failed: {e}")
            raise
    return wrapper


def handle_errors(func):
    """Decorator to handle errors gracefully."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            return func(*args, **kwargs)
        except FileNotFoundError as e:
            return f"Error: File not found - {e}"
        except PermissionError:
            return "Error: Permission denied"
        except json.JSONDecodeError:
            return "Error: Invalid JSON format"
        except Exception as e:
            logger.exception(f"Unexpected error in {func.__name__}")
            return f"Error: {type(e).__name__} - {str(e)}"
    return wrapper


# =============================================================================
# INPUT MODELS (Pydantic Validation)
# =============================================================================

class FileReadInput(BaseModel):
    """Input for reading files."""
    path: str = Field(..., description="File path to read")
    encoding: str = Field(default="utf-8", description="File encoding")
    
    @validator('path')
    def validate_path(cls, v):
        # Security: Prevent path traversal
        if '..' in v or v.startswith('/'):
            raise ValueError("Invalid path: traversal not allowed")
        return v


class FileWriteInput(BaseModel):
    """Input for writing files."""
    path: str = Field(..., description="File path to write")
    content: str = Field(..., description="Content to write")
    append: bool = Field(default=False, description="Append instead of overwrite")
    
    @validator('path')
    def validate_path(cls, v):
        # Check extension
        ext = os.path.splitext(v)[1].lower()
        if ext and ext not in config.ALLOWED_EXTENSIONS:
            raise ValueError(f"Extension {ext} not allowed")
        if '..' in v:
            raise ValueError("Path traversal not allowed")
        return v
    
    @validator('content')
    def validate_content_size(cls, v):
        if len(v.encode()) > config.MAX_FILE_SIZE:
            raise ValueError(f"Content exceeds max size of {config.MAX_FILE_SIZE} bytes")
        return v


class QueryInput(BaseModel):
    """Input for database queries."""
    table: str = Field(..., description="Table name to query")
    filters: Optional[dict] = Field(default=None, description="Query filters")
    limit: int = Field(default=100, ge=1, le=1000, description="Max results")
    offset: int = Field(default=0, ge=0, description="Results offset")


class SearchInput(BaseModel):
    """Input for searching."""
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    max_results: int = Field(default=10, ge=1, le=100, description="Max results")


# =============================================================================
# FILE TOOLS
# =============================================================================

@mcp.tool()
@log_request
@handle_errors
def read_file(input: FileReadInput) -> str:
    """
    Read contents of a file.
    
    Args:
        input: File read parameters (path, encoding)
    
    Returns:
        File contents as string
    """
    full_path = os.path.join(config.DATA_DIR, input.path)
    
    # Security check
    real_path = os.path.realpath(full_path)
    if not real_path.startswith(os.path.realpath(config.DATA_DIR)):
        return "Error: Access denied"
    
    with open(full_path, 'r', encoding=input.encoding) as f:
        return f.read()


@mcp.tool()
@log_request
@handle_errors
def write_file(input: FileWriteInput) -> str:
    """
    Write content to a file.
    
    Args:
        input: File write parameters (path, content, append)
    
    Returns:
        Success message
    """
    full_path = os.path.join(config.DATA_DIR, input.path)
    
    # Security check
    real_path = os.path.realpath(os.path.dirname(full_path) or config.DATA_DIR)
    if not real_path.startswith(os.path.realpath(config.DATA_DIR)):
        return "Error: Access denied"
    
    # Create directory if needed
    os.makedirs(os.path.dirname(full_path) or '.', exist_ok=True)
    
    mode = 'a' if input.append else 'w'
    with open(full_path, mode, encoding='utf-8') as f:
        f.write(input.content)
    
    return f"Successfully {'appended to' if input.append else 'wrote'} {input.path}"


@mcp.tool()
@log_request
@handle_errors
def list_files(directory: str = "") -> str:
    """
    List files in a directory.
    
    Args:
        directory: Directory path (relative to data dir)
    
    Returns:
        JSON list of files with metadata
    """
    full_path = os.path.join(config.DATA_DIR, directory)
    
    # Security check
    real_path = os.path.realpath(full_path)
    if not real_path.startswith(os.path.realpath(config.DATA_DIR)):
        return "Error: Access denied"
    
    if not os.path.isdir(full_path):
        return f"Error: Directory not found: {directory}"
    
    files = []
    for name in os.listdir(full_path):
        file_path = os.path.join(full_path, name)
        stat = os.stat(file_path)
        files.append({
            "name": name,
            "type": "directory" if os.path.isdir(file_path) else "file",
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        })
    
    return json.dumps(files, indent=2)


# =============================================================================
# DATABASE TOOLS (Simulated)
# =============================================================================

# Simulated database
MOCK_DATABASE = {
    "users": [
        {"id": 1, "name": "Alice", "email": "alice@example.com", "role": "admin"},
        {"id": 2, "name": "Bob", "email": "bob@example.com", "role": "user"},
        {"id": 3, "name": "Charlie", "email": "charlie@example.com", "role": "user"},
    ],
    "products": [
        {"id": 1, "name": "Widget A", "price": 29.99, "stock": 100},
        {"id": 2, "name": "Widget B", "price": 49.99, "stock": 50},
    ],
    "orders": [
        {"id": 1, "user_id": 1, "product_id": 1, "quantity": 2, "status": "completed"},
        {"id": 2, "user_id": 2, "product_id": 2, "quantity": 1, "status": "pending"},
    ],
}


@mcp.tool()
@log_request
@handle_errors
def query_table(input: QueryInput) -> str:
    """
    Query a database table.
    
    Args:
        input: Query parameters (table, filters, limit, offset)
    
    Returns:
        Query results as JSON
    """
    if input.table not in MOCK_DATABASE:
        available = list(MOCK_DATABASE.keys())
        return f"Error: Table '{input.table}' not found. Available: {available}"
    
    results = MOCK_DATABASE[input.table].copy()
    
    # Apply filters
    if input.filters:
        filtered = []
        for row in results:
            match = all(
                row.get(k) == v
                for k, v in input.filters.items()
            )
            if match:
                filtered.append(row)
        results = filtered
    
    # Apply pagination
    results = results[input.offset:input.offset + input.limit]
    
    return json.dumps({
        "table": input.table,
        "count": len(results),
        "results": results,
    }, indent=2)


@mcp.tool()
@log_request
def get_table_schema(table: str) -> str:
    """
    Get schema for a database table.
    
    Args:
        table: Table name
    
    Returns:
        Schema information as JSON
    """
    if table not in MOCK_DATABASE:
        return f"Error: Table '{table}' not found"
    
    if not MOCK_DATABASE[table]:
        return json.dumps({"table": table, "columns": []})
    
    sample = MOCK_DATABASE[table][0]
    columns = [
        {"name": k, "type": type(v).__name__}
        for k, v in sample.items()
    ]
    
    return json.dumps({
        "table": table,
        "columns": columns,
        "row_count": len(MOCK_DATABASE[table]),
    }, indent=2)


@mcp.tool()
@log_request
def list_tables() -> str:
    """
    List all available database tables.
    
    Returns:
        JSON list of tables with row counts
    """
    tables = [
        {"name": name, "row_count": len(rows)}
        for name, rows in MOCK_DATABASE.items()
    ]
    return json.dumps(tables, indent=2)


# =============================================================================
# SEARCH TOOL
# =============================================================================

@mcp.tool()
@log_request
@handle_errors
def search(input: SearchInput) -> str:
    """
    Search across all data.
    
    Args:
        input: Search parameters (query, max_results)
    
    Returns:
        Search results as JSON
    """
    query_lower = input.query.lower()
    results = []
    
    # Search database
    for table_name, rows in MOCK_DATABASE.items():
        for row in rows:
            row_str = json.dumps(row).lower()
            if query_lower in row_str:
                results.append({
                    "source": f"database/{table_name}",
                    "data": row,
                })
                if len(results) >= input.max_results:
                    break
        if len(results) >= input.max_results:
            break
    
    return json.dumps({
        "query": input.query,
        "count": len(results),
        "results": results,
    }, indent=2)


# =============================================================================
# RESOURCES
# =============================================================================

@mcp.resource("config://server")
def get_server_config() -> str:
    """Server configuration (non-sensitive)."""
    return json.dumps({
        "name": "ProductionServer",
        "version": "1.0.0",
        "data_dir": config.DATA_DIR,
        "max_file_size": config.MAX_FILE_SIZE,
        "allowed_extensions": list(config.ALLOWED_EXTENSIONS),
    }, indent=2)


@mcp.resource("stats://server")
def get_server_stats() -> str:
    """Server statistics."""
    return json.dumps(ctx.get_stats(), indent=2)


@mcp.resource("schema://database")
def get_database_schema() -> str:
    """Complete database schema."""
    schema = {}
    for table_name, rows in MOCK_DATABASE.items():
        if rows:
            schema[table_name] = {
                "columns": list(rows[0].keys()),
                "row_count": len(rows),
            }
    return json.dumps(schema, indent=2)


# =============================================================================
# PROMPTS
# =============================================================================

@mcp.prompt()
def data_analysis_prompt(question: str) -> str:
    """Generate a data analysis prompt."""
    schema = get_database_schema()
    return f"""You have access to a database with this schema:
{schema}

Please analyze the data to answer: {question}

Use the query_table tool to fetch data, then provide insights.
"""


@mcp.prompt()
def report_generation_prompt(report_type: str, parameters: str = "") -> str:
    """Generate a report prompt."""
    return f"""Generate a {report_type} report.

Parameters: {parameters if parameters else 'None specified'}

Steps:
1. Query relevant data using query_table
2. Analyze the results
3. Format as a clear report with:
   - Executive summary
   - Key findings
   - Recommendations
"""


@mcp.prompt()
def file_analysis_prompt(file_path: str) -> str:
    """Generate a file analysis prompt."""
    return f"""Analyze the file at: {file_path}

Steps:
1. Read the file using read_file
2. Identify the file type and structure
3. Summarize the contents
4. Provide any relevant insights
"""


# =============================================================================
# UTILITY TOOLS
# =============================================================================

@mcp.tool()
def get_current_time() -> str:
    """Get current server time."""
    return datetime.now().isoformat()


@mcp.tool()
def get_server_info() -> str:
    """Get server information and status."""
    return json.dumps({
        "name": "ProductionServer",
        "version": "1.0.0",
        "status": "running",
        "stats": ctx.get_stats(),
    }, indent=2)


# =============================================================================
# RUN SERVER
# =============================================================================

if __name__ == "__main__":
    import sys
    
    # Check for transport type argument
    transport = "stdio"  # default
    port = 8080
    
    for arg in sys.argv[1:]:
        if arg.startswith("--transport="):
            transport = arg.split("=")[1]
        elif arg.startswith("--port="):
            port = int(arg.split("=")[1])
    
    logger.info(f"Starting server with transport={transport}")
    
    if transport == "stdio":
        mcp.run()
    elif transport == "sse":
        mcp.run(transport="sse", port=port)
    else:
        logger.error(f"Unknown transport: {transport}")
        sys.exit(1)
