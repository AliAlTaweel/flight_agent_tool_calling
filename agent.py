"""
agent.py
--------
Core Flight Planning Agent.

Uses LangChain's create_tool_calling_agent + AgentExecutor with
Ollama/llama3.1 and all four custom tools.
LangSmith tracing is enabled automatically via environment variables.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_ollama import ChatOllama

from tools import ALL_TOOLS

# ── Load environment variables ────────────────────────────────────────────────
load_dotenv()


# ── Prompt Template ───────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are SkyAssist, an expert AI flight planning agent for a premium airline.

Your responsibilities:
1. Search Flights – When a user asks about flights, extract the origin, destination,
   date (YYYY-MM-DD), and number of passengers, then call search_flights.
2. Book Flights – Once the user selects a flight, collect the passenger's full name
   and preferred cabin class, then call book_flight. Always confirm details before booking.
3. Handle Complaints – If a user expresses dissatisfaction or wants to raise a formal
   complaint, collect their name, the category, and a detailed description, then call
   file_complaint to save a record.
4. Retrieve Bookings – If a user provides a PNR and wants to check their booking,
   call get_booking.

Guidelines:
- Be professional, empathetic, and concise.
- Always confirm key details (date format, names, route) before calling booking tools.
- If information is missing, ask follow-up questions one at a time.
- Never fabricate flight IDs or prices; always rely on tool output.
- IMPORTANT: When a tool returns output, always copy the COMPLETE tool output verbatim into your reply to the user. Never summarize or omit any part of it.
"""

_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)


# ── LLM ───────────────────────────────────────────────────────────────────────
def _build_llm() -> ChatOllama:
    model = os.getenv("MODEL", "ollama/llama3.1").removeprefix("ollama/")
    base_url = os.getenv("API_BASE", "http://localhost:11434")
    return ChatOllama(
        model=model,
        base_url=base_url,
        temperature=0.2,
    )


# ── Agent Factory ─────────────────────────────────────────────────────────────
def build_agent_executor(verbose: bool = False) -> AgentExecutor:
    """Construct and return a ready-to-use AgentExecutor."""
    llm = _build_llm()
    agent = create_tool_calling_agent(llm=llm, tools=ALL_TOOLS, prompt=_prompt)
    return AgentExecutor(
        agent=agent,
        tools=ALL_TOOLS,
        verbose=verbose,
        handle_parsing_errors=True,
        max_iterations=8,
        return_intermediate_steps=True,
    )


# ── Stateless invoke helper ───────────────────────────────────────────────────
def run_agent(
    user_message: str,
    chat_history: list | None = None,
    executor: AgentExecutor | None = None,
) -> str:
    """Invoke the agent with a user message and optional chat history."""
    if executor is None:
        executor = build_agent_executor()

    result = executor.invoke(
        {
            "input": user_message,
            "chat_history": chat_history or [],
        }
    )

    final_output = result.get("output", "I'm sorry, I couldn't process that request.")

    # If the LLM omitted tool output, prepend the last tool result directly.
    steps = result.get("intermediate_steps", [])
    if steps:
        last_tool_output = str(steps[-1][1])
        if last_tool_output and last_tool_output not in final_output:
            final_output = f"{last_tool_output}\n\n{final_output}"

    return final_output
