"""
services/copilot_service.py
Frontier AI Career Copilot & Technical Interview Coach powered by Microsoft Azure AI Foundry (GPT-4.1-mini).
Provides elite, high-IQ conversational mentoring:
- Progressive hint ladders for active interview questions (Level 1 Nudge -> Level 2 Scaffolding -> Level 3 Deep Dive)
- System Design 5-step frameworks with trade-off matrices
- STAR-method behavioral response transformations (Before vs. After)
- Algorithmic analysis with Big-O Time & Space rigor
- Clean Markdown formatting with code blocks, tables, and actionable next steps
"""

import os
from typing import Dict, Any, List, Optional, Generator
from services.foundry_service import get_foundry_service


DEFAULT_QUICK_PROMPTS = [
    "💡 Hint on my current interview question",
    "⭐ Give me a STAR method example with metrics",
    "🏛️ 5-step System Design framework with trade-offs",
    "⚡ How should I answer 'Tell me about yourself'?",
    "🧠 Big-O complexity & common edge cases checklist",
    "🎯 Top 3 tricky questions for my target role"
]


class CopilotService:
    """Manages high-IQ conversational AI coaching sessions for Interview IQ."""

    def __init__(self):
        self.foundry_service = get_foundry_service()

    def build_system_prompt(self, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Builds a context-aware system prompt tailored to the candidate's exact interview state.
        """
        ctx = context or {}
        role = ctx.get("role", "Software Engineer")
        difficulty = ctx.get("difficulty", "Medium")
        interview_type = ctx.get("interview_type", "Technical")
        current_question = ctx.get("current_question", "")
        stage = ctx.get("stage", "practice")
        user_name = ctx.get("user_name", "Candidate")

        system_prompt = f"""You are the **Interview IQ Elite AI Career Coach & Principal Technical Interviewer** at a top-tier tech company (FAANG / Silicon Valley tier-1).
Your mission is to mentor {user_name} to achieve top 1% interview performance.

### CANDIDATE SESSION TELEMETRY:
- **Candidate:** {user_name}
- **Target Role:** {role}
- **Current Difficulty:** {difficulty}
- **Interview Track:** {interview_type}
- **Platform Stage:** {stage}
"""
        if current_question:
            system_prompt += f"""- **ACTIVE INTERVIEW QUESTION IN PROGRESS:**
"{current_question}"

⚠️ **SPECIAL INSTRUCTION FOR ACTIVE QUESTION HINTS:**
If {user_name} asks for help, hints, or advice on this active question:
1. **DO NOT GIVE AWAY THE FULL SOLUTION IMMEDIATELY.** A true mentor guides the candidate to discover it themselves.
2. Provide a **Progressive Hint Ladder**:
   - **Level 1 (Intuition / Nudge):** What fundamental data structure, algorithm, or architectural pattern applies?
   - **Level 2 (Scaffolding / Edge Cases):** What invariant or boundary condition must be maintained?
   - **Level 3 (Architecture / Complexity):** What is the target Big-O time/space or system scalability bottleneck?
3. Ask a clarifying question back to prompt their thinking!
"""

        system_prompt += """
### COACHING PRINCIPLES & RESPONSE STRUCTURE:
1. **Insightful, Deep & Actionable:** Avoid generic surface-level advice. Give concrete examples, numbers, architectural diagrams (ASCII or Markdown tables), and real-world production gotchas.
2. **Behavioral (STAR Method Mastery):**
   - Teach Situation (15%), Task (15%), Action (50%), Result (20%).
   - Emphasize hard metrics (e.g. "reduced p99 API latency from 450ms to 42ms", "saved $1.2M in annual cloud egress").
   - Offer "Before vs. After" answer upgrades.
3. **System Design Rigor:**
   - Always structure System Design discussions using:
     1. Functional & Non-Functional Requirements (SLAs, Availability, Latency)
     2. Back-of-the-envelope Scale Estimates (QPS, Storage, Bandwidth)
     3. High-Level Architecture (Client -> CDN -> Load Balancer -> API Gateway -> Microservices -> Cache -> DB)
     4. Deep-Dive on Critical Bottlenecks (CAP Theorem, Cache Invalidation, Sharding, Replication)
4. **Coding & Algorithms:**
   - Always state explicit Time Complexity $O(T)$ and Space Complexity $O(S)$.
   - Highlight boundary conditions: null/empty inputs, single element, large inputs ($10^5$), integer overflow.
   - Provide idiomatic, clean Python/Go/Java code with inline comments when code is requested.
5. **Interview IQ Platform Knowledge:**
   - Understand the platform: Azure AI Foundry (GPT-4.1-mini) adaptive question generation, Azure AI Speech neural TTS/STT, and rubric scoring across Rigor, Relevance, Depth, and Delivery.
6. **Formatting:**
   - Use crisp Markdown with bold headers, bullet lists, code blocks with syntax highlighting, and callout quotes.
   - Be inspiring, sharp, concise, and empowering.

### 🛑 STRICT DOMAIN BOUNDARY & ZERO-HALLUCINATION POLICY:
You are EXCLUSIVELY an AI Technical Interview & Career Coach for Interview IQ.
Your ONLY valid topics are:
1. Interview preparation, technical mock interview guidance, system design, coding problems, algorithms, data structures, and computer science concepts.
2. Behavioral interview frameworks (STAR method), leadership principles, and technical resume/career mentoring.
3. The candidate's active interview question, session telemetry, or platform usage.

ABSOLUTE REFUSAL RULE FOR OUT-OF-CONTEXT QUESTIONS:
If the user asks ANY question that is outside of career coaching, technical interview preparation, software engineering, or the active interview context (such as: general world trivia, recipes/cooking, politics, entertainment, sports scores, weather, creative writing unrelated to jobs, medical/legal advice, or casual chit-chat unrelated to careers):
- YOU MUST NOT ANSWER OR HALLUCINATE ABOUT THE TOPIC.
- YOU MUST REFUSE TO ANSWER POLITELY AND DIRECTLY:
  "I am Interview IQ's AI Career & Technical Interview Coach. I am strictly focused on interview preparation, system design, coding problems, technical concepts, and career mentoring. I cannot answer questions outside of this context.

How can I help you prepare for your technical or behavioral interview today?"
"""
        return system_prompt

    def stream_copilot_response(
        self,
        messages: List[Dict[str, str]],
        context: Optional[Dict[str, Any]] = None
    ) -> Generator[str, None, None]:
        """
        Streams a response token-by-token from Azure AI Foundry GPT-4.1-mini.
        """
        system_prompt = self.build_system_prompt(context)

        # Build payload with system prompt followed by conversation history
        full_messages = [{"role": "system", "content": system_prompt}]
        for m in messages:
            if m.get("role") in ("user", "assistant"):
                full_messages.append({
                    "role": m["role"],
                    "content": m.get("content", "")
                })

        try:
            client = self.foundry_service.get_openai_client()
            model_name = self.foundry_service.model_name or "gpt-4.1-mini"
            stream = client.chat.completions.create(
                model=model_name,
                messages=full_messages,
                temperature=0.3,
                stream=True
            )

            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            yield f"\n\n*(Notice: Azure AI Foundry connection status: {str(e)})*"

    def get_copilot_response(
        self,
        messages: List[Dict[str, str]],
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Synchronous fallback to get the full response string.
        """
        chunks = []
        for chunk in self.stream_copilot_response(messages, context):
            chunks.append(chunk)
        return "".join(chunks)


# Global singleton instance
_copilot_instance: Optional[CopilotService] = None


def get_copilot_service() -> CopilotService:
    global _copilot_instance
    if _copilot_instance is None:
        _copilot_instance = CopilotService()
    return _copilot_instance
