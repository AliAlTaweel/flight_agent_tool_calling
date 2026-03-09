"""
app.py
------
Gradio chat interface for the SkyAssist Flight Planning Agent.

Run:
    python app.py
    # or with auto-reload during development:
    gradio app.py
"""

from __future__ import annotations

import gradio as gr
from langchain_core.messages import AIMessage, HumanMessage

from agent import build_agent_executor, run_agent

# Build a single shared executor (avoids re-initialising the LLM on each turn)
_executor = build_agent_executor(verbose=True)


# ── Chat logic ─────────────────────────────────────────────────────────────────
def respond(
    user_message: str,
    history: list[dict],
) -> tuple[str, list[dict]]:
    """Process one user turn and return the updated history."""
    if not user_message.strip():
        return "", history

    # Convert Gradio messages-format history to LangChain message objects
    lc_history: list = []
    for msg in history:
        if msg["role"] == "user":
            lc_history.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            lc_history.append(AIMessage(content=msg["content"]))

    bot_reply = run_agent(
        user_message=user_message,
        chat_history=lc_history,
        executor=_executor,
    )

    history = history + [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": bot_reply},
    ]
    return "", history


# ── Gradio UI ─────────────────────────────────────────────────────────────────
_DESCRIPTION = """
## ✈️ SkyAssist – AI Flight Planning Agent
Powered by **Google Gemini** + **LangChain** tool-calling.

**What I can do:**
- 🔍 Search available flights by route and date
- 🎫 Book flights and issue confirmations
- 📝 File formal complaints and save them as `.txt` records
- 📋 Retrieve existing bookings by PNR

**Try saying:**  
*"Find me flights from London to New York on 2025-08-10 for 2 passengers"*
"""

_EXAMPLES = [
    ["Search for flights from JFK to LAX on 2025-09-01 for 1 passenger"],
    ["Book flight FL4823 for Jane Doe, Economy class, from JFK to LAX on 2025-09-01"],
    ["I want to raise a complaint about my delayed baggage on flight FL1234"],
    ["What flights are available from Dubai to Paris on 2025-10-15?"],
    ["Show me my booking for PNR AB1234"],
]

with gr.Blocks(title="SkyAssist – Flight Agent") as demo:

    gr.Markdown(_DESCRIPTION)

    chatbot = gr.Chatbot(
        label="SkyAssist",
        avatar_images=(
            None,  # user avatar (None = default)
            "https://api.dicebear.com/7.x/bottts/svg?seed=skyassist&backgroundColor=0ea5e9",
        ),
        height=520,
    )

    with gr.Row():
        msg_box = gr.Textbox(
            placeholder="Type your message here… (e.g. 'Find flights from NYC to Miami on 2025-07-20')",
            show_label=False,
            scale=9,
            container=False,
        )
        send_btn = gr.Button("Send ✈️", scale=1, variant="primary")

    gr.Examples(
        examples=_EXAMPLES,
        inputs=msg_box,
        label="💡 Example prompts",
    )

    clear_btn = gr.Button("🗑️ Clear conversation", variant="secondary", size="sm")

    # ── Event wiring ───────────────────────────────────────────────────────────
    send_btn.click(
        fn=respond,
        inputs=[msg_box, chatbot],
        outputs=[msg_box, chatbot],
    )

    msg_box.submit(
        fn=respond,
        inputs=[msg_box, chatbot],
        outputs=[msg_box, chatbot],
    )

    clear_btn.click(fn=lambda: ([], ""), outputs=[chatbot, msg_box])  # [] = empty messages list


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        theme=gr.themes.Soft(
            primary_hue="blue",
            secondary_hue="sky",
            font=gr.themes.GoogleFont("Inter"),
        ),
        css="""
        .gradio-container { max-width: 860px; margin: auto; }
        footer { display: none !important; }
        """,
    )