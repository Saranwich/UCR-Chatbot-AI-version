# UCR Smart City Chatbot - Architecture & AI Integration Context

This document provides a deep-dive architectural context for the UCR (Urban Complaint & Reporting) Smart City Chatbot. It is intended to brief AI assistants (like Claude) on the technical history, the target V2 architecture, and the immediate Proof of Concept (PoC) requirements.

## 1. Project Background (UCR)
UCR is a citizen-facing LINE Official Account Chatbot. Its primary purpose is to allow citizens to report urban infrastructure issues (e.g., broken pipes, potholes, electrical hazards) and answer municipal surveys. The system collects these reports and displays them on an internal Dashboard for city management.

## 2. Technical Context: Version 1 (Legacy / Stable)
V1 is currently stable and archived in the `old/1.0` Git branch. The main development branch is `Ai-chatbot-version`.
- **Stack:** Python, FastAPI.
- **Workflow:** LINE Webhook -> `app/main.py` -> `app/services/survey_service.py`.
- **Logic:** Rule-based. If a user types a specific keyword (or triggers a LIFF app), a hardcoded JSON survey flow (e.g., `fdg210626.json`) is initiated.
- **Features:** Handles atomic state replies, emergency fallback replies, image storage, and dashboard data fetching.

## 3. Technical Context: Version 2 (The AI Evolution)
We are evolving the rigid survey tree into a **Natural Language AI Receptionist** using Google Gemini (Gemini 2.5 Flash via the `google-genai` SDK).
We are NOT doing a big-bang rewrite. We are evolving core components iteratively.

### 3.1 The Target AI Flow
1. **Intercept:** Text/Image/Location events from the LINE Webhook are routed to a new `ai_handler.py` instead of the old rule-based engine.
2. **Conversation:** Gemini chats naturally with the citizen to understand the issue.
3. **Data Extraction:** Once Gemini determines it has enough context, it will extract structured data:
   - `category` (e.g., Road, Water, Electricity, Public Order)
   - `severity` (Scale 1-5 or Low/Medium/High)
   - `summary` (Concise description of the problem)
   - `location` (Extracted from text or LINE location event)
4. **Action (Tool Use):** Gemini invokes a `save_report` function (function calling) with the extracted data.
5. **Database Strategy (Crucial):** To avoid premature database schema lock-in, the Python backend will take the extracted JSON from Gemini and store it directly into a `JSONB` column (e.g., in an `ai_reports` table). We will normalize this data into dedicated columns later.

## 4. Immediate Task: The Sandbox PoC
Integrating AI directly into the V1 webhook is too complex due to LINE API constraints and existing logic.
Therefore, our immediate task is to build a **Clean Slate PoC (Proof of Concept)** in a separate directory/project.

### PoC Technical Requirements & Scope
- **Tech Stack:** Python 3, FastAPI, Uvicorn, `google-genai` (Gemini 2.5 Flash), Pydantic, python-dotenv.
- **Constraints:** NO LINE API code. NO real Database connections. Only mock functions.
- **Deliverables:**

**1. `main.py` (The API Router)**
- A single `POST /chat` endpoint.
- Accepts a JSON body containing `user_id` and `message`.
- Maintains an in-memory dictionary to store Chat History per `user_id` (e.g., `Dict[str, List[dict]]`) to maintain context across requests.

**2. `ai_handler.py` (The Brain)**
- Initializes the Gemini client (`genai.Client(api_key=...)`).
- Appends the new user message to the history and sends the entire array to `client.models.generate_content` (model `gemini-2.5-flash`).
- **Tool Use (Function Calling) Implementation:**
  - Define a function declaration for `save_report(category: str, severity: int, summary: str)` and pass it via the `tools` config.
  - Inspect the response. If `response.function_calls` is present, extract the arguments, print them to the console (simulating a DB JSONB save), and append a `function_response` part back into the history so Gemini knows the action succeeded.
  - Return Gemini's final text response back to the FastAPI endpoint.

---
**Instructions for the AI assistant:**
Act as a mentor, not a code generator. The developer is learning and will write `requirements.txt`, `main.py`, and `ai_handler.py` themselves. Explain concepts, review their code, and unblock them — fulfilling ONLY the PoC requirements above. Keep guidance clear and ready to test via Swagger UI.
