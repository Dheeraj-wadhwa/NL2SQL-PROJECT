import os
from dotenv import load_dotenv

# Correct Vanna 2.x Imports
from vanna.core.agent.agent import Agent as VannaAgent
from vanna.integrations.local.agent_memory.in_memory import DemoAgentMemory
from vanna.tools.run_sql import RunSqlTool
from vanna.tools.visualize_data import VisualizeDataTool
from vanna.core.registry import ToolRegistry
from vanna.integrations.sqlite.sql_runner import SqliteRunner
from vanna.integrations.google.gemini import GeminiLlmService
from vanna.core.user.models import User
from vanna.core.user.resolver import UserResolver
from vanna.core.user.request_context import RequestContext

class DummyUserResolver(UserResolver):
    async def resolve_user(self, request_context: RequestContext) -> User:
        return User(id="default_user", email="test@example.com")
load_dotenv()

def get_vanna_components():
    """
    Initializes and returns the Vanna Agent, Memory, and Database Runner
    for the exact Vanna 2.0 configuration.
    """
    # 1. Setup Database Runner for the established Clinic SQLite DB
    runner = SqliteRunner(database_path='clinic.db')
    
    # 2. Setup LLM (Google Gemini)
    api_key = os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", ""))
    if not api_key:
        print("WARNING: Neither GEMINI_API_KEY nor GOOGLE_API_KEY were found in .env. The agent will require one to function.")
    
    llm = GeminiLlmService(api_key=api_key) if api_key else GeminiLlmService()

    # 3. Setup Agent Memory (To store schemas and seeded Q-SQL pairs)
    memory = DemoAgentMemory()

    # 4. Setup Tools
    sql_tool = RunSqlTool(sql_runner=runner)
    viz_tool = VisualizeDataTool()
    tool_registry = ToolRegistry()
    tool_registry.register_local_tool(sql_tool, access_groups=[])
    tool_registry.register_local_tool(viz_tool, access_groups=[])

    # 5. Connect modules to the base Agent wrapper
    # Note: Depending on the exact Agent constructor in this 2.x build, attributes map appropriately
    user_resolver = DummyUserResolver()
    agent = VannaAgent(
        llm_service=llm,
        agent_memory=memory,
        tool_registry=tool_registry,
        user_resolver=user_resolver
    )

    return agent, memory, runner

if __name__ == "__main__":
    print("Initializing components...")
    agent, memory, runner = get_vanna_components()
    print("Vanna 2.0 components successfully registered!")
