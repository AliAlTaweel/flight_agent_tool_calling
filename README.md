# ✈️ SkyAssist – AI Flight Planning Agent

A production-ready, tool-calling AI agent that helps passengers **search flights**, **make bookings**, and **file complaints** — built with **LangChain**, **Google Gemini**, and **Gradio**.

---

## 📁 Project Structure

```
flight-agent/
│
├── app.py                  # Gradio chat UI (entry point)
├── agent.py                # Agent factory + prompt template + run_agent helper
│
├── tools/
│   ├── __init__.py         # Exports ALL_TOOLS list
│   ├── flight_search.py    # Tool: search_flights
│   ├── flight_booking.py   # Tool: book_flight + get_booking
│   └── complaint.py        # Tool: file_complaint
│
├── tests/
│   ├── __init__.py
│   └── test_tools.py       # Pytest unit tests for all tools
│
├── complaints/             # Auto-created at runtime; stores complaint .txt files
│
├── .env.example            # Template for environment variables (copy → .env)
├── .env                    # ⚠️ Your secrets — never commit this file
├── .gitignore
├── requirements.txt
└── README.md
```

> **Where to put each file:** copy the directory tree above exactly.  
> All source files live at the root of `flight-agent/` except tools (in `tools/`) and tests (in `tests/`).

---

## 🚀 Quick Start

### 1. Clone / create the project

```bash
git clone <repo-url> flight-agent
cd flight-agent
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in your credentials:

```ini
# Required
GOOGLE_API_KEY=AIza...          # Google AI Studio → https://aistudio.google.com/

# LangSmith (optional but recommended for tracing)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=lsv2_...      # https://smith.langchain.com/ → Settings → API Keys
LANGCHAIN_PROJECT=flight-agent

# App settings
COMPLAINTS_DIR=complaints       # directory where complaint .txt files are saved
```

#### Getting API Keys

| Service | URL | Notes |
|---------|-----|-------|
| Google Gemini | https://aistudio.google.com/ | Free tier available |
| LangSmith | https://smith.langchain.com/ | Free tier; enables tracing |

### 5. Run the app

```bash
python app.py
```

Then open **http://localhost:7860** in your browser.

---

## 🛠️ Tools

| Tool | File | Purpose |
|------|------|---------|
| `search_flights` | `tools/flight_search.py` | Search available flights by route + date |
| `book_flight` | `tools/flight_booking.py` | Book a specific flight, returns PNR |
| `get_booking` | `tools/flight_booking.py` | Look up an existing booking by PNR |
| `file_complaint` | `tools/complaint.py` | Save a passenger complaint as a `.txt` file |

> **Note:** `search_flights` and `book_flight` use deterministic dummy data — no external API key required. Swap the internals for a real flight API (e.g. Amadeus, Skyscanner) to productionise.

---

## 💬 Example Conversations

```
User:  Find me flights from JFK to LAX on 2025-08-10 for 2 passengers
Agent: [calls search_flights] → lists available flights with prices

User:  Book FL4823 for Jane Doe, Business class
Agent: [calls book_flight] → "✅ Booking Confirmed! PNR: XY9K2A"

User:  I want to complain about my delayed baggage on flight FL1234
Agent: [calls file_complaint] → saves complaint_{name}_{timestamp}_{id}.txt
                              → "📝 Complaint filed! ID: A3F2C1B9"

User:  Show me booking AB1234
Agent: [calls get_booking] → displays booking details
```

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

Expected output:

```
tests/test_tools.py::TestSearchFlights::test_returns_flights_for_valid_route   PASSED
tests/test_tools.py::TestSearchFlights::test_invalid_date_format               PASSED
tests/test_tools.py::TestSearchFlights::test_past_date_rejected                PASSED
tests/test_tools.py::TestSearchFlights::test_multiple_passengers               PASSED
tests/test_tools.py::TestSearchFlights::test_case_insensitive_airports         PASSED
tests/test_tools.py::TestBookFlight::test_successful_booking                   PASSED
tests/test_tools.py::TestBookFlight::test_empty_name_rejected                  PASSED
tests/test_tools.py::TestBookFlight::test_business_class_more_expensive_than_economy PASSED
tests/test_tools.py::TestGetBooking::test_retrieve_after_booking               PASSED
tests/test_tools.py::TestGetBooking::test_unknown_pnr_returns_error            PASSED
tests/test_tools.py::TestFileComplaint::test_creates_txt_file                  PASSED
tests/test_tools.py::TestFileComplaint::test_empty_name_rejected               PASSED
tests/test_tools.py::TestFileComplaint::test_empty_text_rejected               PASSED
tests/test_tools.py::TestFileComplaint::test_complaint_id_in_response          PASSED
```

> Tests do **not** require a Google API key — they test the tool logic directly.

---

## 🔭 LangSmith Tracing

When `LANGCHAIN_TRACING_V2=true` and `LANGCHAIN_API_KEY` are set, every agent run is automatically traced at **https://smith.langchain.com/** under the project `flight-agent`.

You will see:
- Full tool call chain (inputs + outputs)
- Token usage per step
- Latency breakdown
- Error traces

---

## 🏗️ Architecture

```
User Input (Gradio)
       │
       ▼
  app.py::respond()
       │
       ▼
  agent.py::run_agent()
       │
       ▼
  AgentExecutor (LangChain)
       │
       ├─► search_flights  (tools/flight_search.py)
       ├─► book_flight     (tools/flight_booking.py)
       ├─► get_booking     (tools/flight_booking.py)
       └─► file_complaint  (tools/complaint.py)
       │
       ▼
  Google Gemini 1.5 Flash
  (tool-calling mode)
       │
       ▼
  Response → Gradio Chat UI
```

---

## 🔧 Configuration Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GOOGLE_API_KEY` | ✅ | — | Gemini API key |
| `LANGCHAIN_TRACING_V2` | ❌ | `false` | Enable LangSmith tracing |
| `LANGCHAIN_ENDPOINT` | ❌ | — | LangSmith endpoint |
| `LANGCHAIN_API_KEY` | ❌ | — | LangSmith API key |
| `LANGCHAIN_PROJECT` | ❌ | `default` | LangSmith project name |
| `COMPLAINTS_DIR` | ❌ | `complaints` | Directory for complaint files |

---

## 📦 Dependencies

| Package | Purpose |
|---------|---------|
| `langchain` | Agent framework + tool abstraction |
| `langchain-google-genai` | Gemini integration |
| `langchain-core` | Prompts, messages, tools |
| `langsmith` | Observability & tracing |
| `gradio` | Chat web UI |
| `python-dotenv` | `.env` file loading |
| `pydantic` | Data validation |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Add tests for new tools in `tests/test_tools.py`
4. Run `pytest tests/ -v` and ensure all tests pass
5. Open a pull request

---

## 📜 License

MIT License – see `LICENSE` for details.