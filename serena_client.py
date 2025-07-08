"""
SerenaClient - A Python client for interacting with Serena MCP server
to analyze Python codebases.
"""

import asyncio
import json
import logging
from typing import Optional, Dict, List, Any
from pathlib import Path
from contextlib import AsyncExitStack
from dataclasses import dataclass

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    import httpx
    import json
except ImportError:
    print("MCP library not found. Install with: pip install mcp httpx")
    raise


@dataclass
class AnalysisResult:
    """Container for code analysis results"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class SerenaClient:
    """
    Client for connecting to Serena MCP server and analyzing Python codebases.
    
    Usage:
        client = SerenaClient()
        await client.start()
        result = await client.activate_project("/path/to/codebase")
        analysis = await client.analyze_code("find all classes")
        await client.stop()
    """
    
    def __init__(self, server_command: str = "serena-mcp-server"):
        """
        Initialize SerenaClient.
        
        Args:
            server_command: Command to start Serena MCP server
        """
        self.server_command = server_command
        self.exit_stack = AsyncExitStack()
        self.session: Optional[ClientSession] = None
        self.current_project: Optional[str] = None
        self.available_tools: List[str] = []
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    async def start(self) -> bool:
        """
        Connect to Serena MCP server.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Configure server parameters for Serena
            server_params = StdioServerParameters(
                command="uvx",
                args=["--from", "git+https://github.com/oraios/serena", self.server_command],
                env=None
            )
            
            self.logger.info("Starting Serena MCP server...")
            
            # Establish stdio transport
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            read, write = stdio_transport
            
            # Create client session
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(read, write)
            )
            
            # Initialize connection
            await self.session.initialize()
            
            # Get available tools
            tools_response = await self.session.list_tools()
            self.available_tools = [tool.name for tool in tools_response.tools]
            
            self.logger.info(f"Connected to Serena with tools: {self.available_tools}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Serena: {e}")
            return False
    
    async def stop(self):
        """Stop the connection and cleanup resources."""
        try:
            await self.exit_stack.aclose()
            self.logger.info("Serena client stopped")
        except Exception as e:
            self.logger.error(f"Error stopping client: {e}")
    
    async def activate_project(self, project_path: str) -> AnalysisResult:
        """
        Activate a project for analysis.
        
        Args:
            project_path: Path to the Python codebase directory
            
        Returns:
            AnalysisResult: Result of project activation
        """
        if not self.session:
            return AnalysisResult(
                success=False,
                message="Not connected to Serena server",
                error="Call start() first"
            )
        
        # Validate project path
        path = Path(project_path)
        if not path.exists():
            return AnalysisResult(
                success=False,
                message="Project path does not exist",
                error=f"Path not found: {project_path}"
            )
        
        if not path.is_dir():
            return AnalysisResult(
                success=False,
                message="Project path is not a directory",
                error=f"Not a directory: {project_path}"
            )
        
        try:
            # Use absolute path
            abs_path = str(path.absolute())
            
            # Call Serena to activate project (using correct parameter name)
            result = await self.session.call_tool(
                "activate_project",
                arguments={"project": abs_path}
            )
            
            self.current_project = abs_path
            self.logger.info(f"Activated project: {abs_path}")
            
            return AnalysisResult(
                success=True,
                message=f"Successfully activated project: {abs_path}",
                data={"project_path": abs_path, "result": result}
            )
            
        except Exception as e:
            self.logger.error(f"Failed to activate project: {e}")
            return AnalysisResult(
                success=False,
                message="Failed to activate project",
                error=str(e)
            )
    
    async def analyze_code(self, query: str, **kwargs) -> AnalysisResult:
        """
        Analyze code in the current project.
        
        Args:
            query: Analysis query (e.g., "find all classes", "show imports")
            **kwargs: Additional parameters for analysis
            
        Returns:
            AnalysisResult: Analysis results
        """
        if not self.session:
            return AnalysisResult(
                success=False,
                message="Not connected to Serena server",
                error="Call start() first"
            )
        
        if not self.current_project:
            return AnalysisResult(
                success=False,
                message="No project activated",
                error="Call activate_project() first"
            )
        
        try:
            # Prepare analysis parameters
            params = {
                "query": query,
                "project_path": self.current_project,
                **kwargs
            }
            
            # Use appropriate tool based on query type
            tool_name = self._select_analysis_tool(query)
            
            result = await self.session.call_tool(tool_name, arguments=params)
            
            return AnalysisResult(
                success=True,
                message=f"Analysis completed for: {query}",
                data={"query": query, "result": result}
            )
            
        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")
            return AnalysisResult(
                success=False,
                message="Analysis failed",
                error=str(e)
            )
    
    async def search_code(self, pattern: str, file_types: List[str] = None) -> AnalysisResult:
        """
        Search for code patterns in the project.
        
        Args:
            pattern: Search pattern (regex or text)
            file_types: List of file extensions to search (e.g., ['.py', '.js'])
            
        Returns:
            AnalysisResult: Search results
        """
        if not self.session:
            return AnalysisResult(
                success=False,
                message="Not connected to Serena server",
                error="Call start() first"
            )
        
        try:
            result = await self.session.call_tool(
                "search_for_pattern",
                arguments={"substring_pattern": pattern}
            )
            
            return AnalysisResult(
                success=True,
                message=f"Search completed for pattern: {pattern}",
                data={"pattern": pattern, "result": result}
            )
            
        except Exception as e:
            return AnalysisResult(
                success=False,
                message="Search failed",
                error=str(e)
            )
    
    async def get_file_structure(self) -> AnalysisResult:
        """
        Get the file structure of the current project.
        
        Returns:
            AnalysisResult: Project file structure
        """
        if not self.session:
            return AnalysisResult(
                success=False,
                message="Not connected to Serena server",
                error="Call start() first"
            )
        
        try:
            result = await self.session.call_tool(
                "list_dir",
                arguments={
                    "relative_path": ".",
                    "recursive": True
                }
            )
            
            return AnalysisResult(
                success=True,
                message="File structure retrieved",
                data={"structure": result}
            )
            
        except Exception as e:
            return AnalysisResult(
                success=False,
                message="Failed to get file structure",
                error=str(e)
            )
    
    async def find_functions(self, name_pattern: str = None) -> AnalysisResult:
        """
        Find functions in the project.
        
        Args:
            name_pattern: Optional pattern to filter function names
            
        Returns:
            AnalysisResult: Found functions
        """
        if not self.session:
            return AnalysisResult(
                success=False,
                message="Not connected to Serena server",
                error="Call start() first"
            )
        
        try:
            if name_pattern:
                # Search for specific function using pattern search
                result = await self.session.call_tool(
                    "search_for_pattern",
                    arguments={"substring_pattern": f"def {name_pattern}"}
                )
            else:
                # Get all symbols overview
                result = await self.session.call_tool(
                    "get_symbols_overview",
                    arguments={"relative_path": "."}
                )
            
            return AnalysisResult(
                success=True,
                message=f"Functions search completed",
                data={"pattern": name_pattern, "result": result}
            )
            
        except Exception as e:
            return AnalysisResult(
                success=False,
                message="Function search failed",
                error=str(e)
            )
    
    async def find_classes(self, name_pattern: str = None) -> AnalysisResult:
        """
        Find classes in the project.
        
        Args:
            name_pattern: Optional pattern to filter class names
            
        Returns:
            AnalysisResult: Found classes
        """
        if not self.session:
            return AnalysisResult(
                success=False,
                message="Not connected to Serena server",
                error="Call start() first"
            )
        
        try:
            if name_pattern:
                # Search for specific class using pattern search
                result = await self.session.call_tool(
                    "search_for_pattern",
                    arguments={"substring_pattern": f"class {name_pattern}"}
                )
            else:
                # Get all symbols overview
                result = await self.session.call_tool(
                    "get_symbols_overview",
                    arguments={"relative_path": "."}
                )
            
            return AnalysisResult(
                success=True,
                message=f"Classes search completed",
                data={"pattern": name_pattern, "result": result}
            )
            
        except Exception as e:
            return AnalysisResult(
                success=False,
                message="Class search failed",
                error=str(e)
            )
    
    async def analyze_imports(self) -> AnalysisResult:
        """
        Analyze imports and dependencies in the project.
        
        Returns:
            AnalysisResult: Import analysis
        """
        if not self.session:
            return AnalysisResult(
                success=False,
                message="Not connected to Serena server",
                error="Call start() first"
            )
        
        try:
            # Search for import statements
            result = await self.session.call_tool(
                "search_for_pattern",
                arguments={"substring_pattern": "import"}
            )
            
            return AnalysisResult(
                success=True,
                message="Import analysis completed",
                data={"result": result}
            )
            
        except Exception as e:
            return AnalysisResult(
                success=False,
                message="Import analysis failed",
                error=str(e)
            )
    
    async def get_code_metrics(self) -> AnalysisResult:
        """
        Get code quality metrics for the project.
        
        Returns:
            AnalysisResult: Code metrics
        """
        if not self.session:
            return AnalysisResult(
                success=False,
                message="Not connected to Serena server",
                error="Call start() first"
            )
        
        try:
            # Get symbols overview as a basic metric
            result = await self.session.call_tool(
                "get_symbols_overview",
                arguments={"relative_path": "."}
            )
            
            return AnalysisResult(
                success=True,
                message="Code metrics calculated",
                data={"result": result}
            )
            
        except Exception as e:
            return AnalysisResult(
                success=False,
                message="Code metrics calculation failed",
                error=str(e)
            )
    
    def _select_analysis_tool(self, query: str) -> str:
        """
        Select the appropriate Serena tool based on the query.
        
        Args:
            query: Analysis query
            
        Returns:
            str: Tool name to use
        """
        query_lower = query.lower()
        
        # Map query types to actual Serena tools
        if "search" in query_lower or "pattern" in query_lower:
            return "search_for_pattern"
        elif "structure" in query_lower or "tree" in query_lower or "list" in query_lower:
            return "list_dir"
        elif "symbol" in query_lower or "class" in query_lower or "function" in query_lower:
            return "get_symbols_overview"
        elif "find" in query_lower:
            return "find_symbol"
        else:
            # Default to symbols overview
            return "get_symbols_overview"
    
    async def list_available_tools(self) -> List[str]:
        """
        Get list of available tools from Serena.
        
        Returns:
            List[str]: Available tool names
        """
        return self.available_tools
    
    def is_connected(self) -> bool:
        """Check if connected to Serena server."""
        return self.session is not None
    
    def get_current_project(self) -> Optional[str]:
        """Get the currently activated project path."""
        return self.current_project
    
    async def call_tool_directly(self, tool_name: str, arguments: Dict[str, Any] = None) -> AnalysisResult:
        """
        Call any Serena MCP tool directly.
        
        Args:
            tool_name: Name of the MCP tool to call
            arguments: Dictionary of arguments to pass to the tool
            
        Returns:
            AnalysisResult: Tool execution result
        """
        if not self.session:
            return AnalysisResult(
                success=False,
                message="Not connected to Serena server",
                error="Call start() first"
            )
        
        if tool_name not in self.available_tools:
            return AnalysisResult(
                success=False,
                message=f"Tool '{tool_name}' not available",
                error=f"Available tools: {self.available_tools}"
            )
        
        try:
            result = await self.session.call_tool(tool_name, arguments=arguments or {})
            return AnalysisResult(
                success=True,
                message=f"Tool '{tool_name}' executed successfully",
                data={"tool": tool_name, "arguments": arguments, "result": result}
            )
        except Exception as e:
            return AnalysisResult(
                success=False,
                message=f"Tool '{tool_name}' execution failed",
                error=str(e)
            )
    
    async def think_about_collected_information(self) -> AnalysisResult:
        """
        Ask Serena to think about the collected information.
        
        Returns:
            AnalysisResult: Serena's analysis of collected information
        """
        return await self.call_tool_directly("think_about_collected_information")
    
    async def think_about_task_adherence(self) -> AnalysisResult:
        """
        Ask Serena to think about task adherence.
        
        Returns:
            AnalysisResult: Serena's analysis of task adherence
        """
        return await self.call_tool_directly("think_about_task_adherence")
    
    async def think_about_whether_you_are_done(self) -> AnalysisResult:
        """
        Ask Serena to evaluate if the current task is complete.
        
        Returns:
            AnalysisResult: Serena's evaluation of task completion
        """
        return await self.call_tool_directly("think_about_whether_you_are_done")
    
    async def summarize_changes(self) -> AnalysisResult:
        """
        Ask Serena to summarize changes made.
        
        Returns:
            AnalysisResult: Summary of changes
        """
        return await self.call_tool_directly("summarize_changes")
    
    async def read_file(self, file_path: str) -> AnalysisResult:
        """
        Read a file using Serena.
        
        Args:
            file_path: Path to the file to read
            
        Returns:
            AnalysisResult: File contents
        """
        return await self.call_tool_directly("read_file", {"relative_path": file_path})
    
    async def write_memory(self, key: str, content: str) -> AnalysisResult:
        """
        Write to Serena's memory.
        
        Args:
            key: Memory key
            content: Content to store
            
        Returns:
            AnalysisResult: Memory write result
        """
        return await self.call_tool_directly("write_memory", {"memory_file_name": key, "content": content})
    
    async def read_memory(self, key: str) -> AnalysisResult:
        """
        Read from Serena's memory.
        
        Args:
            key: Memory key to read
            
        Returns:
            AnalysisResult: Memory content
        """
        return await self.call_tool_directly("read_memory", {"memory_file_name": key})
    
    async def list_memories(self) -> AnalysisResult:
        """
        List all available memories.
        
        Returns:
            AnalysisResult: List of memory keys
        """
        return await self.call_tool_directly("list_memories")
    
    async def execute_shell_command(self, command: str) -> AnalysisResult:
        """
        Execute a shell command via Serena.
        
        Args:
            command: Shell command to execute
            
        Returns:
            AnalysisResult: Command output
        """
        return await self.call_tool_directly("execute_shell_command", {"command": command})
    
    # === Project Management ===
    
    async def get_active_project(self) -> AnalysisResult:
        """
        Gets the name of the currently active project and lists existing projects.
        
        Returns:
            AnalysisResult: Active project info and project list
        """
        return await self.call_tool_directly("get_active_project")
    
    async def check_onboarding_performed(self) -> AnalysisResult:
        """
        Checks whether project onboarding was already performed.
        
        Returns:
            AnalysisResult: Onboarding status
        """
        return await self.call_tool_directly("check_onboarding_performed")
    
    async def onboarding(self) -> AnalysisResult:
        """
        Performs onboarding (identifying project structure and essential tasks).
        
        Returns:
            AnalysisResult: Onboarding results
        """
        return await self.call_tool_directly("onboarding")
    
    async def get_current_config(self) -> AnalysisResult:
        """
        Prints the current configuration including active modes, tools, and context.
        
        Returns:
            AnalysisResult: Current configuration
        """
        return await self.call_tool_directly("get_current_config")
    
    async def switch_modes(self, modes: List[str]) -> AnalysisResult:
        """
        Activates modes by providing a list of their names.
        
        Args:
            modes: List of mode names to activate
            
        Returns:
            AnalysisResult: Mode switch result
        """
        return await self.call_tool_directly("switch_modes", {"modes": modes})
    
    # === File Operations ===
    
    async def create_text_file(self, file_path: str, content: str) -> AnalysisResult:
        """
        Creates/overwrites a file in the project directory.
        
        Args:
            file_path: Path to the file to create
            content: Content to write to the file
            
        Returns:
            AnalysisResult: File creation result
        """
        return await self.call_tool_directly("create_text_file", {
            "relative_path": file_path, 
            "content": content
        })
    
    async def delete_lines(self, file_path: str, start_line: int, end_line: int) -> AnalysisResult:
        """
        Deletes a range of lines within a file.
        
        Args:
            file_path: Path to the file
            start_line: Start line number
            end_line: End line number
            
        Returns:
            AnalysisResult: Line deletion result
        """
        return await self.call_tool_directly("delete_lines", {
            "relative_path": file_path,
            "start_line": start_line,
            "end_line": end_line
        })
    
    async def replace_lines(self, file_path: str, start_line: int, end_line: int, content: str) -> AnalysisResult:
        """
        Replaces a range of lines within a file with new content.
        
        Args:
            file_path: Path to the file
            start_line: Start line number
            end_line: End line number
            content: New content to replace with
            
        Returns:
            AnalysisResult: Line replacement result
        """
        return await self.call_tool_directly("replace_lines", {
            "relative_path": file_path,
            "start_line": start_line,
            "end_line": end_line,
            "content": content
        })
    
    async def insert_at_line(self, file_path: str, line_number: int, content: str) -> AnalysisResult:
        """
        Inserts content at a given line in a file.
        
        Args:
            file_path: Path to the file
            line_number: Line number to insert at
            content: Content to insert
            
        Returns:
            AnalysisResult: Line insertion result
        """
        return await self.call_tool_directly("insert_at_line", {
            "relative_path": file_path,
            "line_number": line_number,
            "content": content
        })
    
    # === Symbol Operations ===
    
    async def find_symbol(self, name: str, symbol_type: str = None, local_only: bool = False) -> AnalysisResult:
        """
        Performs a global (or local) search for symbols with/containing a given name.
        
        Args:
            name: Symbol name or substring to search for
            symbol_type: Optional symbol type filter (e.g., "class", "function")
            local_only: If True, search only in current file
            
        Returns:
            AnalysisResult: Found symbols
        """
        args = {"name": name}
        if symbol_type:
            args["type"] = symbol_type
        if local_only:
            args["local_only"] = local_only
        return await self.call_tool_directly("find_symbol", args)
    
    async def find_referencing_symbols(self, file_path: str, line: int, column: int, symbol_type: str = None) -> AnalysisResult:
        """
        Finds symbols that reference the symbol at the given location.
        
        Args:
            file_path: Path to the file containing the symbol
            line: Line number of the symbol
            column: Column number of the symbol
            symbol_type: Optional filter by symbol type
            
        Returns:
            AnalysisResult: Referencing symbols
        """
        args = {
            "relative_path": file_path,
            "line": line,
            "column": column
        }
        if symbol_type:
            args["type"] = symbol_type
        return await self.call_tool_directly("find_referencing_symbols", args)
    
    async def find_referencing_code_snippets(self, file_path: str, line: int, column: int) -> AnalysisResult:
        """
        Finds code snippets in which the symbol at the given location is referenced.
        
        Args:
            file_path: Path to the file containing the symbol
            line: Line number of the symbol
            column: Column number of the symbol
            
        Returns:
            AnalysisResult: Code snippets with references
        """
        return await self.call_tool_directly("find_referencing_code_snippets", {
            "relative_path": file_path,
            "line": line,
            "column": column
        })
    
    async def replace_symbol_body(self, file_path: str, symbol_name: str, new_content: str) -> AnalysisResult:
        """
        Replaces the full definition of a symbol.
        
        Args:
            file_path: Path to the file containing the symbol
            symbol_name: Name of the symbol to replace
            new_content: New content for the symbol
            
        Returns:
            AnalysisResult: Symbol replacement result
        """
        return await self.call_tool_directly("replace_symbol_body", {
            "relative_path": file_path,
            "symbol_name": symbol_name,
            "content": new_content
        })
    
    async def insert_before_symbol(self, file_path: str, symbol_name: str, content: str) -> AnalysisResult:
        """
        Inserts content before the beginning of the definition of a given symbol.
        
        Args:
            file_path: Path to the file containing the symbol
            symbol_name: Name of the symbol
            content: Content to insert
            
        Returns:
            AnalysisResult: Content insertion result
        """
        return await self.call_tool_directly("insert_before_symbol", {
            "relative_path": file_path,
            "symbol_name": symbol_name,
            "content": content
        })
    
    async def insert_after_symbol(self, file_path: str, symbol_name: str, content: str) -> AnalysisResult:
        """
        Inserts content after the end of the definition of a given symbol.
        
        Args:
            file_path: Path to the file containing the symbol
            symbol_name: Name of the symbol
            content: Content to insert
            
        Returns:
            AnalysisResult: Content insertion result
        """
        return await self.call_tool_directly("insert_after_symbol", {
            "relative_path": file_path,
            "symbol_name": symbol_name,
            "content": content
        })
    
    # === Memory Operations (already implemented above) ===
    
    async def delete_memory(self, key: str) -> AnalysisResult:
        """
        Deletes a memory from Serena's project-specific memory store.
        
        Args:
            key: Memory key to delete
            
        Returns:
            AnalysisResult: Memory deletion result
        """
        return await self.call_tool_directly("delete_memory", {"memory_file_name": key})
    
    # === System Operations ===
    
    async def restart_language_server(self) -> AnalysisResult:
        """
        Restarts the language server (may be necessary when edits not through Serena happen).
        
        Returns:
            AnalysisResult: Language server restart result
        """
        return await self.call_tool_directly("restart_language_server")
    
    async def initial_instructions(self) -> AnalysisResult:
        """
        Gets the initial instructions for the current project.
        
        Returns:
            AnalysisResult: Initial instructions
        """
        return await self.call_tool_directly("initial_instructions")
    
    async def prepare_for_new_conversation(self) -> AnalysisResult:
        """
        Provides instructions for preparing for a new conversation.
        
        Returns:
            AnalysisResult: Preparation instructions
        """
        return await self.call_tool_directly("prepare_for_new_conversation")
    
    # === Helper Methods ===
    
    def check_project_indexing(self, project_path: str) -> Dict[str, Any]:
        """
        Check if a project has been indexed and provide recommendations.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Dict with indexing status and recommendations
        """
        from pathlib import Path
        
        project_dir = Path(project_path)
        serena_dir = project_dir / ".serena"
        
        status = {
            "project_path": str(project_dir.absolute()),
            "serena_dir_exists": serena_dir.exists(),
            "is_configured": False,
            "is_indexed": False,
            "recommendations": []
        }
        
        if serena_dir.exists():
            status["is_configured"] = True
            
            # Check for project config
            project_yml = serena_dir / "project.yml"
            if project_yml.exists():
                status["has_project_config"] = True
            
            # Check for cache (indicates indexing)
            cache_dir = serena_dir / "cache"
            if cache_dir.exists() and list(cache_dir.glob("*")):
                status["is_indexed"] = True
                status["recommendations"].append("✅ Project appears to be indexed")
            else:
                status["recommendations"].append(
                    "💡 Consider indexing for better performance:\n"
                    "   uvx --from git+https://github.com/oraios/serena index-project"
                )
        else:
            status["recommendations"].extend([
                "ℹ️  Project not yet configured with Serena",
                "🚀 Activate the project first, then consider indexing for large projects"
            ])
        
        return status
    
    async def activate_project_with_guidance(self, project_path: str) -> AnalysisResult:
        """
        Activate a project with helpful guidance and recommendations.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            AnalysisResult: Enhanced activation result with guidance
        """
        from pathlib import Path
        
        # Check indexing status first
        indexing_status = self.check_project_indexing(project_path)
        
        # Activate the project
        abs_path = str(Path(project_path).absolute())
        result = await self.activate_project(abs_path)
        
        # Enhance the result with guidance
        if result.success:
            guidance = {
                "activation_result": result.data,
                "indexing_status": indexing_status,
                "recommendations": indexing_status["recommendations"]
            }
            
            # Add additional recommendations based on project size
            try:
                project_dir = Path(project_path)
                python_files = list(project_dir.rglob("*.py"))
                if len(python_files) > 50:
                    guidance["recommendations"].append(
                        f"📈 Large project detected ({len(python_files)} Python files) - "
                        "indexing highly recommended for optimal performance"
                    )
            except Exception:
                pass
            
            result.data = guidance
            result.message = f"Project activated successfully with guidance: {abs_path}"
        
        return result


# Context manager support
class SerenaClientContext:
    """Context manager for SerenaClient"""
    
    def __init__(self, client: SerenaClient):
        self.client = client
    
    async def __aenter__(self):
        await self.client.start()
        return self.client
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.stop()


# Example usage and testing
async def example_usage():
    """Example usage of SerenaClient"""
    
    # Method 1: Manual connection management
    client = SerenaClient()
    
    try:
        # Start connection
        if not await client.start():
            print("Failed to connect to Serena")
            return
        
        # Activate a project
        result = await client.activate_project("/home/guci/aiProjects/CodeAnalysis")
        print(f"Project activation: {result.message}")
        
        if result.success:
            # Analyze the codebase
            analysis = await client.find_classes()
            print(f"Classes found: {analysis.message}")
            
            # Search for specific patterns
            search_result = await client.search_code("class.*Client")
            print(f"Search result: {search_result.message}")
            
            # Get file structure
            structure = await client.get_file_structure()
            print(f"File structure: {structure.message}")
        
    finally:
        await client.stop()
    
    print("\n" + "="*50 + "\n")
    
    # Method 2: Using context manager
    async with SerenaClientContext(SerenaClient()) as client:
        result = await client.activate_project("/home/guci/aiProjects/CodeAnalysis")
        if result.success:
            # Perform analysis
            functions = await client.find_functions("main")
            print(f"Main functions: {functions.message}")


if __name__ == "__main__":
    asyncio.run(example_usage())