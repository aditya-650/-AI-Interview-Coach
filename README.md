# Interview IQ: AI-Powered Interview Coach 🎯

**Interview IQ** is a college AI prototype for realistic, grounded, and adaptive technical and behavioral mock interviews. It uses **Microsoft Azure AI Foundry** (Agent Service, `gpt-4.1-mini`, Vector Store / File Search RAG) and **Azure AI Speech** (Speech-to-Text) with an interactive **Streamlit** frontend.

---

## 1. Project Overview

Preparing for technical and HR interviews requires personalized practice grounded in a candidate's actual projects, technical skills, and resume. Existing tools often present static question banks or simulated evaluations.

**Interview IQ** delivers a live, interactive interview loop:
1. The candidate uploads their resume, project report, or job description (PDF, DOCX, TXT).
2. The document is indexed into a dedicated Microsoft Foundry Vector Store.
3. The AI interviewer generates targeted questions grounded directly in the uploaded material.
4. The candidate responds naturally by speaking into their microphone.
5. Azure AI Speech transcribes the response to text.
6. The AI evaluates technical correctness, relevance, depth, and clarity, providing concise feedback and a numerical score.
7. Subsequent questions adapt based on previous answers (increasing difficulty for strong answers, pivoting to foundational concepts for struggles).
8. A comprehensive final performance report is generated with category breakdowns, strengths, improvement areas, and recommended study topics.

---

## 2. Key Features

- **Document Grounding (RAG via Microsoft Foundry File Search)**: Ingests PDF, DOCX, or TXT into Foundry Vector Stores. The AI cites and questions candidate projects directly.
- **Real Speech Recognition (Azure AI Speech)**: Captures voice input directly through the browser or local microphone, transcribing spoken answers using Azure Cognitive Services Speech SDK.
- **Editable Transcript Review**: Displays transcribed speech to the candidate before submission, allowing quick corrections of technical acronyms or phonetic edge cases.
- **Responsible AI Evaluation**: Objectively assesses technical concepts, structure, and communication without making psychological judgments, personality claims, or employment fitness verdicts.
- **Adaptive Difficulty Progression**: Adjusts question depth dynamically based on performance across Easy, Medium, and Hard tiers.
- **Comprehensive Post-Interview Analytics**: Delivers multi-metric scores (Overall, Technical Knowledge, Answer Quality, Communication), question-by-question breakdowns, and targeted study roadmaps.
- **Resource Lifecycle Management**: Automatically cleans up session vector stores from Foundry upon completion or restart to prevent cloud clutter.

---

## 3. Architecture

```
Candidate (Browser / Mic)
       │
       ▼
   Streamlit UI (app.py)
       │
       ├── Document Upload (PDF / DOCX / TXT)
       │         │
       │         ▼
       │   document_service.py ──► Azure AI Foundry Vector Store (File Search Indexing)
       │
       ├── Question Generation & RAG
       │         │
       │         ▼
       │   interview_service.py ──► Microsoft Foundry Agent (AI-Interview-Coach / gpt-4.1-mini)
       │
       ├── Speech Capture & Recognition
       │         │
       │         ▼
       │   speech_service.py ──► Azure AI Speech (Speech-to-Text)
       │
       ├── Answer Evaluation & Adaptive Logic
       │         │
       │         ▼
       │   interview_service.py ──► Foundry Agent (Evaluation & Adaptive Difficulty)
       │
       └── Final Report Synthesis
                 │
                 ▼
           interview_service.py ──► Comprehensive Report & Actionable Preparation Roadmap
```

---

## 4. Technology Stack

- **Frontend**: Streamlit 1.34+ (Python)
- **AI Platform**: Microsoft Azure AI Foundry (`azure-ai-projects`, `openai`)
- **LLM / Foundation Model**: `gpt-4.1-mini`
- **Embeddings**: `text-embedding-3-small` (Foundry Managed Vector Stores)
- **Speech-to-Text**: Azure Cognitive Services Speech (`azure-cognitiveservices-speech`)
- **Authentication**: Azure Identity `DefaultAzureCredential` via Azure CLI (`az login`)
- **Document Processing**: Foundry Native File Search with optional local inspection (`pypdf`, `python-docx`)
- **Environment Management**: `python-dotenv`

---

## 5. Azure Resources Required

1. **Azure Subscription**: (e.g. Azure for Students, Pay-As-You-Go)
2. **Microsoft Azure AI Foundry Project**:
   - Deployed model: `gpt-4.1-mini`
   - Embedding model: `text-embedding-3-small`
   - Agent: `AI-Interview-Coach` (with File Search enabled)
3. **Azure AI Speech Resource**:
   - Cognitive Services Speech service in your preferred Azure region (e.g. `uaenorth`, `eastus`).

---

## 6. Environment Variables

Create a `.env` file in the project root:

```env
# Microsoft Foundry Project Endpoint
FOUNDRY_PROJECT_ENDPOINT=https://<your-foundry-resource>.services.ai.azure.com/api/projects/<your-project-name>
FOUNDRY_MODEL=gpt-4.1-mini
FOUNDRY_AGENT_NAME=AI-Interview-Coach

# Azure AI Speech Configuration
AZURE_SPEECH_KEY=<your-azure-speech-resource-key>
AZURE_SPEECH_REGION=<your-azure-speech-region>
```

> **Note**: An example template is provided in [.env.example](file:///.env.example). Never commit your `.env` file to version control.

---

## 7. Installation

1. **Clone the repository / navigate to project root**:
   ```powershell
   cd c:\Users\adity\Desktop\coding\projects\AI103
   ```

2. **(Optional) Create and activate a Python virtual environment**:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. **Install dependencies**:
   ```powershell
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

---

## 8. Azure CLI Authentication

This application uses `DefaultAzureCredential()` to authenticate against Microsoft Foundry without hardcoded access tokens or credentials in source code.

Authenticate locally with the Azure CLI:
```powershell
az login
```
Verify that your active subscription is selected:
```powershell
az account show
```
If you have multiple subscriptions, select the appropriate one:
```powershell
az account set --subscription "<Your-Subscription-Name-or-ID>"
```

---

## 9. Running the Application

Launch the Streamlit web application:
```powershell
streamlit run app.py
```
Streamlit will launch local browser access at `http://localhost:8501`.

---

## 10. Testing & Verification

### Diagnostic Health Check
Run the diagnostic script to verify your connection to Foundry and Azure Speech:
```powershell
python test_connection.py
```

### Full Automated Pipeline Integration Test
Run the end-to-end integration test which tests document upload, vector store indexing, grounded question generation, simulated speech recognition, answer scoring, and report generation:
```powershell
python test_integration.py
```

---

## 11. Known Limitations

- **Microphone Browser Permissions**: When recording in Streamlit (`st.audio_input`), the browser must grant microphone permissions to `localhost`.
- **Speech Accent & Domain Terms**: Specialized technical jargon (e.g. rare library names) may occasionally require quick editing in the editable transcript box before submission.
- **Session Duration**: Vector stores are tied to active interview sessions and cleaned up on restart. If an interview is left idle for hours, temporary files may expire.

---

## 12. Responsible AI Considerations

- **Educational Purpose Only**: Interview IQ is strictly designed as an interview preparation and educational practice tool. It is **not** a hiring decision system.
- **No Psychological Judgments**: The AI model is strictly prompted never to assess personality traits, mental states, honesty, or confidence.
- **Objective Evaluation**: Feedback is constrained to technical correctness, conceptual depth, relevance, and articulation clarity.

---

## 13. Future Improvements

- **Real-Time Video / Visual Interviewing**: Integration with Azure Vision for eye-contact and non-verbal pacing tips.
- **Custom Interview Rubrics**: Allowing university professors or recruiters to define custom scoring criteria and required technical benchmarks.
- **Exportable PDF Report**: Downloadable summary report with charts and study recommendations for student portfolios.
