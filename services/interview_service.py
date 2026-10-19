"""
services/interview_service.py
Core interview logic orchestrator:
- Grounded question generation via Foundry Agent + File Search
- Strict answer evaluation (Responsible AI compliant)
- Adaptive difficulty progression
- Final comprehensive performance report generation
"""

import json
from typing import Dict, Any, List, Optional
from services.foundry_service import get_foundry_service
from utils.helpers import parse_evaluation_response, parse_final_report_response


ROLE_FALLBACK_QUESTIONS = {
    ("AI/ML Engineer", "Easy"): [
        "Can you explain the difference between supervised and unsupervised learning, providing one real-world production example of each?",
        "What is gradient descent, and how does the choice of learning rate impact model convergence and loss stability?",
        "Explain the purpose of train/validation/test splits and why cross-validation is used in model development."
    ],
    ("AI/ML Engineer", "Medium"): [
        "Can you explain the difference between overfitting and underfitting in a machine learning model, and describe two concrete regularization techniques you have implemented in production?",
        "How do you evaluate and optimize a machine learning model facing severe class imbalance in a fraud detection or anomaly detection dataset?",
        "Explain the core architectural differences between a standard Recurrent Neural Network (RNN) and a Transformer architecture, focusing on the self-attention mechanism."
    ],
    ("AI/ML Engineer", "Hard"): [
        "Walk me through how you would architect a low-latency vector similarity search indexing pipeline serving 50M embeddings with sub-15ms p99 retrieval.",
        "How do you mitigate catastrophic forgetting and handle parameter-efficient fine-tuning (LoRA / QLoRA) when adapting 70B+ parameter LLMs for domain-specific agent workflows?",
        "Design a real-time distributed feature store capable of handling 50k writes/sec while preventing training-serving skew."
    ],
    ("Software Engineer", "Easy"): [
        "What is the difference between a process and a thread, and how does multi-threading improve application throughput?",
        "Explain how a hash map works internally, including collision resolution strategies and average vs. worst-case time complexities.",
        "What is the difference between stack memory and heap memory, and how are variables allocated across them?"
    ],
    ("Software Engineer", "Medium"): [
        "Design a concurrency-safe in-memory cache with an LRU eviction policy, explaining your choice of data structures and lock granularity.",
        "Explain how database indexing works using B+ Trees, and describe a scenario where adding an index could degrade query performance.",
        "Walk me through how you would refactor a monolithic REST service into an event-driven microservices architecture using Apache Kafka or RabbitMQ."
    ],
    ("Software Engineer", "Hard"): [
        "Design a multi-region active-active Kubernetes failover architecture with automated health probes and cross-cluster service discovery.",
        "How would you design a distributed consensus protocol like Raft or Paxos, and how does it guarantee safety during network partitions?",
        "Architect a distributed transactional system supporting ACID guarantees across heterogeneous datastores using the 2-Phase Commit or Saga pattern."
    ],
    ("Distributed Systems Architect", "Easy"): [
        "Explain the fundamentals of horizontal vs. vertical scaling, and describe when each strategy is most appropriate.",
        "What is a reverse proxy and how does it differ from a forward proxy in modern cloud architectures?"
    ],
    ("Distributed Systems Architect", "Medium"): [
        "Explain the trade-offs between strong consistency and eventual consistency in distributed data stores according to the PACELC theorem.",
        "How do you design an idempotent API endpoint for payment processing to ensure duplicate requests do not result in double charges?"
    ],
    ("Distributed Systems Architect", "Hard"): [
        "Walk me through how you would architect a distributed real-time rate limiter handling 100k requests/sec with Redis and the Token Bucket algorithm.",
        "How do you architect a globally distributed database that maintains low-latency writes while preventing data divergence and split-brain scenarios?"
    ],
    ("Python Developer", "Easy"): [
        "Explain the difference between mutable and immutable types in Python, and how they behave when passed as arguments to functions.",
        "How do Python list comprehensions work, and how do they differ in memory efficiency compared to generator expressions?"
    ],
    ("Python Developer", "Medium"): [
        "Explain how Python's Global Interpreter Lock (GIL) affects multi-threaded CPU-bound programs versus I/O-bound programs, and how to circumvent it.",
        "Describe how Python's context managers work under the hood using `__enter__` and `__exit__`, and how to implement one using `contextlib`."
    ],
    ("Python Developer", "Hard"): [
        "How does Python's garbage collection mechanism handle cyclic references, and how would you profile and optimize memory leaks in a production FastAPI or Celery service?",
        "Explain how Python's `asyncio` event loop schedules coroutines, tasks, and future callbacks, and how blocking calls can silently starve the event loop."
    ],
    ("Data Scientist", "Easy"): [
        "What is the difference between Type I and Type II errors in hypothesis testing, and which is typically more critical to minimize in healthcare diagnostics?",
        "Explain how linear regression estimates coefficients using Ordinary Least Squares (OLS), and state the key Gauss-Markov assumptions."
    ],
    ("Data Scientist", "Medium"): [
        "How would you design an end-to-end A/B testing experiment for a recommendation system, and how do you calculate minimum sample size and detect p-hacking?",
        "Explain the mathematical differences between bagging (Random Forests) and boosting (XGBoost/LightGBM), and their respective biases and variances."
    ],
    ("Data Scientist", "Hard"): [
        "How do you detect and mitigate covariate shift and concept drift in a streaming predictive model deployed in high-frequency production environments?",
        "Design a causal inference framework to measure the true incrementality of marketing campaigns when randomized control trials (RCTs) are infeasible."
    ],
    ("Product Manager", "Medium"): [
        "Walk me through how you prioritize a product roadmap when engineering, sales, and executive stakeholders have conflicting high-priority demands.",
        "How do you define the North Star Metric for a two-sided marketplace, and what guardrail metrics do you track alongside it?"
    ],
    ("Engineering Manager", "Medium"): [
        "How do you manage an underperforming senior engineer who is technically gifted but creates friction within team code reviews and planning sessions?",
        "Walk me through your framework for making build-versus-buy architectural decisions under tight delivery deadlines."
    ],
    ("Data Analyst", "Easy"): [
        "Explain the difference between a left join and an inner join in SQL, and give a real-world use case for each.",
        "How do you identify and handle outliers in a dataset before building a dashboard or report?"
    ],
    ("Data Analyst", "Medium"): [
        "How would you design a sales funnel analysis dashboard in SQL from raw event data, defining conversion metrics across each stage?",
        "Explain the difference between cohort analysis and A/B testing, and when you would apply each in a product analytics context."
    ],
    ("Data Analyst", "Hard"): [
        "How would you design a self-serve analytics platform for non-technical business stakeholders while ensuring data governance, accuracy, and query performance?",
        "Describe how you would investigate a sudden 30% drop in DAU (Daily Active Users) using SQL, BI tools, and cross-functional stakeholder interviews."
    ]
}


class InterviewService:
    """Manages the lifecycle of an AI-driven mock interview."""

    def __init__(self):
        self.foundry_service = get_foundry_service()

    def _get_agent_config(self) -> Dict[str, Any]:
        """Retrieves model name and agent instructions from Foundry."""
        agent_info = self.foundry_service.get_agent_details()
        return {
            "model": agent_info.get("model", "gpt-4.1-mini"),
            "agent_instructions": agent_info.get("instructions", "")
        }

    @staticmethod
    def _is_valid_interview_question(text: str) -> bool:
        """Validates that a generated question is legitimate and not an AI refusal/policy block."""
        if not text or not isinstance(text, str):
            return False
        clean = text.strip()
        if len(clean) < 15:
            return False
        lower = clean.lower()
        refusal_signatures = [
            "cannot assist",
            "can't assist",
            "cannot fulfill",
            "can't fulfill",
            "cannot comply",
            "unable to comply",
            "i am sorry",
            "i'm sorry",
            "as an ai",
            "as a language model",
            "against my safety",
            "violates my policy",
            "cannot generate",
            "apologize, but"
        ]
        for sig in refusal_signatures:
            if sig in lower:
                return False
        return True

    def _get_fallback_question(
        self,
        role: str,
        difficulty: str,
        interview_type: str = "Technical",
        question_index: int = 1
    ) -> str:
        """Returns a high-IQ curated question if model generation fails or triggers a safety refusal."""
        key = (role, difficulty)
        questions = ROLE_FALLBACK_QUESTIONS.get(key)
        
        if not questions:
            for (r, d), q_list in ROLE_FALLBACK_QUESTIONS.items():
                if r.lower() in role.lower() or role.lower() in r.lower():
                    if d.lower() == difficulty.lower():
                        questions = q_list
                        break
        
        if not questions:
            for (r, d), q_list in ROLE_FALLBACK_QUESTIONS.items():
                if r.lower() in role.lower() or role.lower() in r.lower():
                    questions = q_list
                    break
        
        if not questions:
            questions = ROLE_FALLBACK_QUESTIONS.get(("Software Engineer", difficulty), [
                "Walk me through the most technically challenging project you have engineered, focusing on the core architectural trade-offs, bottlenecks encountered, and quantifiable outcomes achieved."
            ])
            
        idx = max(0, question_index - 1) % len(questions)
        return questions[idx]

    def generate_first_question(
        self,
        role: str,
        difficulty: str,
        interview_type: str,
        vector_store_id: Optional[str] = None
    ) -> str:
        """
        Generates the first interview question grounded in the candidate's uploaded document
        and tailored to their selected profile and difficulty.
        """
        openai_client = self.foundry_service.get_openai_client()
        cfg = self._get_agent_config()

        tools = []
        if vector_store_id:
            tools.append({
                "type": "file_search",
                "vector_store_ids": [vector_store_id]
            })

        system_prompt = (
            "You are an expert AI Technical and Behavioral Interviewer. "
            "Your task is to generate the FIRST interview question for a candidate.\n\n"
            f"TARGET ROLE: {role}\n"
            f"STARTING DIFFICULTY: {difficulty}\n"
            f"INTERVIEW TYPE: {interview_type}\n\n"
            "INSTRUCTIONS:\n"
            "1. If a document (resume, project report, or study material) is provided via file_search, "
            "search it thoroughly. Formulate a realistic, specific opening question grounded directly "
            "in the candidate's actual projects, skills, technologies, or experience mentioned in the document.\n"
            "2. If the document does not contain relevant experience for this role, or if no document was provided, "
            "ask a standard foundational interview question appropriate for the role and difficulty level. "
            "DO NOT hallucinate or pretend information came from the document if it did not.\n"
            "3. Ask ONLY ONE single question. Do not ask multi-part compound questions.\n"
            "4. Do NOT output greetings like 'Welcome to the interview!'. Return ONLY the direct question text."
        )

        user_prompt = (
            f"Please generate question #1 for a candidate interviewing for the position of {role} "
            f"with {difficulty} difficulty in a {interview_type} interview format. "
            "Ground the question in the uploaded document if available."
        )

        kwargs = {
            "model": cfg["model"],
            "instructions": system_prompt,
            "input": user_prompt
        }
        try:
            response = openai_client.responses.create(**kwargs)
            text = response.output_text.strip()
            if self._is_valid_interview_question(text):
                return text
            return self._get_fallback_question(role, difficulty, interview_type, 1)
        except Exception as e:
            print("Question generation fallback triggered:", e)
            return self._get_fallback_question(role, difficulty, interview_type, 1)

    def evaluate_answer(
        self,
        question: str,
        candidate_answer: str,
        role: str,
        difficulty: str,
        vector_store_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluates the candidate's answer based on technical correctness, relevance, completeness,
        clarity, and depth. Strictly follows Responsible AI guidelines.
        """
        openai_client = self.foundry_service.get_openai_client()
        cfg = self._get_agent_config()

        tools = []
        if vector_store_id:
            tools.append({
                "type": "file_search",
                "vector_store_ids": [vector_store_id]
            })

        system_prompt = (
            "You are an objective AI Interview Evaluator assessing a candidate's answer.\n\n"
            "CRITERIA TO EVALUATE:\n"
            "- Technical Correctness: Factual accuracy of concepts, tools, architectures, or methods.\n"
            "- Relevance: Directly addresses what was asked.\n"
            "- Completeness & Depth: Mentions key considerations, tradeoffs, or implementation steps.\n"
            "- Clarity: Structure, concise articulation, and logical flow.\n\n"
            "STRICT RESPONSIBLE AI GUIDELINES:\n"
            "- Provide objective, educational feedback on the content of the answer.\n"
            "- DO NOT make psychological judgments.\n"
            "- DO NOT claim to measure intelligence, personality, confidence, mental state, honesty, or suitability for employment.\n"
            "- This is an interview practice tool, NOT a hiring decision system.\n\n"
            "OUTPUT FORMAT:\n"
            "You must respond with a VALID JSON object matching this exact schema:\n"
            "{\n"
            '  "score": <float between 1.0 and 10.0>,\n'
            '  "what_well": ["Bullet point 1", "Bullet point 2"],\n'
            '  "what_improve": ["Bullet point 1", "Bullet point 2"]\n'
            "}\n"
            "Do not include extra conversational text outside the JSON."
        )

        user_prompt = (
            f"ROLE: {role}\n"
            f"DIFFICULTY LEVEL: {difficulty}\n"
            f"QUESTION ASKED: {question}\n"
            f"CANDIDATE'S TRANSCRIPT/ANSWER: {candidate_answer}\n\n"
            "Evaluate this answer objectively and return JSON."
        )

        kwargs = {
            "model": cfg["model"],
            "instructions": system_prompt,
            "input": user_prompt
        }
        if tools:
            kwargs["tools"] = tools

        response = openai_client.responses.create(**kwargs)

        return parse_evaluation_response(response.output_text)

    def generate_next_adaptive_question(
        self,
        role: str,
        current_difficulty: str,
        interview_type: str,
        history: List[Dict[str, Any]],
        question_index: int,
        total_questions: int,
        vector_store_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates the next interview question adaptively based on:
        - Previous questions asked (ensuring no repeats)
        - Previous candidate answers and scores
        - Grounded document context
        - Adaptive difficulty shift (increase if strong, follow-up if partial, simpler if weak)
        """
        openai_client = self.foundry_service.get_openai_client()
        cfg = self._get_agent_config()

        tools = []
        if vector_store_id:
            tools.append({
                "type": "file_search",
                "vector_store_ids": [vector_store_id]
            })

        # Determine difficulty adjustment based on the most recent score
        last_item = history[-1] if history else {}
        last_score = last_item.get("score", 7.0)

        difficulty_ladder = ["Easy", "Medium", "Hard"]
        current_idx = difficulty_ladder.index(current_difficulty) if current_difficulty in difficulty_ladder else 1

        adaptation_guidance = ""
        new_difficulty = current_difficulty

        if last_score >= 8.0:
            # Strong answer: increase difficulty if possible
            if current_idx < len(difficulty_ladder) - 1:
                new_difficulty = difficulty_ladder[current_idx + 1]
                adaptation_guidance = (
                    f"The candidate gave a strong answer (Score: {last_score}/10). "
                    f"Increase difficulty from {current_difficulty} to {new_difficulty}. "
                    "Ask a more advanced architectural, edge-case, or performance question."
                )
            else:
                adaptation_guidance = (
                    f"The candidate performed strongly on Hard level (Score: {last_score}/10). "
                    "Challenge them with a deep practical scenario or complex design tradeoff."
                )
        elif last_score < 6.0:
            # Weak answer: ask simpler or clarifying foundational question
            if current_idx > 0:
                new_difficulty = difficulty_ladder[current_idx - 1]
                adaptation_guidance = (
                    f"The candidate struggled with the previous question (Score: {last_score}/10). "
                    f"Lower difficulty from {current_difficulty} to {new_difficulty} or ask a foundational concept "
                    "to help them regain confidence and test core understanding."
                )
            else:
                adaptation_guidance = (
                    f"The candidate struggled with the previous question (Score: {last_score}/10). "
                    "Ask a simpler, foundational clarifying question."
                )
        else:
            # Score 6.0 - 7.9: Partially correct, ask related follow-up
            adaptation_guidance = (
                f"The candidate's previous answer was partially correct (Score: {last_score}/10). "
                "Maintain the current difficulty and ask a targeted follow-up exploring practical application or nuance."
            )

        # Build history context summary
        history_summary = []
        for i, h in enumerate(history, 1):
            q_text = h.get("question", "")
            a_text = h.get("answer", "")
            s_val = h.get("score", "N/A")
            history_summary.append(
                f"Q{i}: {q_text}\n"
                f"Answer {i}: {a_text[:300]}...\n"
                f"Score {i}: {s_val}/10"
            )
        history_str = "\n\n".join(history_summary)

        system_prompt = (
            "You are an expert AI Technical Interviewer conducting an adaptive mock interview.\n\n"
            f"TARGET ROLE: {role}\n"
            f"INTERVIEW TYPE: {interview_type}\n"
            f"CURRENT DIFFICULTY: {new_difficulty}\n"
            f"PROGRESS: Question {question_index} of {total_questions}\n\n"
            "ADAPTATION LOGIC:\n"
            f"{adaptation_guidance}\n\n"
            "RULES:\n"
            "1. DO NOT repeat any previous questions or topics already thoroughly covered.\n"
            "2. Ground the question in the candidate's uploaded document (resume/projects) via file_search where relevant.\n"
            "3. Ask ONLY ONE question. Do not ask compound multi-part questions.\n"
            "4. Return ONLY the question text without conversational preambles or greeting phrases."
        )

        user_prompt = (
            f"Previous Interview History:\n{history_str}\n\n"
            f"Please generate Question #{question_index} for the candidate."
        )

        kwargs = {
            "model": cfg["model"],
            "instructions": system_prompt,
            "input": user_prompt
        }
        try:
            response = openai_client.responses.create(**kwargs)
            text = response.output_text.strip()
            if not self._is_valid_interview_question(text):
                text = self._get_fallback_question(role, new_difficulty, interview_type, question_index)
        except Exception as e:
            print("Adaptive question generation fallback triggered:", e)
            text = self._get_fallback_question(role, new_difficulty, interview_type, question_index)

        return {
            "question": text,
            "new_difficulty": new_difficulty
        }

    def generate_final_report(
        self,
        role: str,
        difficulty: str,
        interview_type: str,
        history: List[Dict[str, Any]],
        vector_store_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generates the comprehensive final interview report dynamically synthesized
        by the AI from all questions, answers, and scores.
        """
        openai_client = self.foundry_service.get_openai_client()
        cfg = self._get_agent_config()

        # Compile detailed transcript
        full_transcript_parts = []
        for i, item in enumerate(history, 1):
            full_transcript_parts.append(
                f"--- Question {i} ---\n"
                f"Question: {item.get('question', '')}\n"
                f"Candidate Answer: {item.get('answer', '')}\n"
                f"Score: {item.get('score', 0)}/10\n"
                f"Positives: {', '.join(item.get('what_well', []))}\n"
                f"Areas to Improve: {', '.join(item.get('what_improve', []))}\n"
            )
        full_transcript = "\n".join(full_transcript_parts)

        system_prompt = (
            "You are a Senior Technical Hiring Manager and Coach generating a final post-interview report.\n\n"
            "EVALUATION GUIDELINES:\n"
            "- Analyze the candidate's performance across all questions holistically.\n"
            "- Compute fair percentage scores out of 100 for:\n"
            "  1. overall_score (weighted composite out of 100)\n"
            "  2. technical_knowledge (technical accuracy and depth out of 100)\n"
            "  3. answer_quality (relevance, thoroughness, examples out of 100)\n"
            "  4. communication (clarity, structure, articulation out of 100)\n"
            "- Summarize key strengths observed.\n"
            "- Summarize clear areas for improvement.\n"
            "- Provide concise per-question summaries.\n"
            "- Recommend 3 to 5 high-impact preparation topics or study materials.\n\n"
            "RESPONSIBLE AI COMPLIANCE:\n"
            "- Evaluate only knowledge, communication of ideas, and problem-solving content.\n"
            "- Do NOT claim to measure intelligence, personality, psychological traits, or employment fitness.\n"
            "- This is an interview coaching tool.\n\n"
            "OUTPUT FORMAT:\n"
            "You must return ONLY a JSON object with this exact structure:\n"
            "{\n"
            '  "overall_score": 82,\n'
            '  "technical_knowledge": 85,\n'
            '  "answer_quality": 80,\n'
            '  "communication": 80,\n'
            '  "strengths": ["Strength 1", "Strength 2", "Strength 3"],\n'
            '  "areas_for_improvement": ["Area 1", "Area 2", "Area 3"],\n'
            '  "question_performance": [\n'
            '    {\n'
            '      "question_num": 1,\n'
            '      "question": "...",\n'
            '      "answer_summary": "Brief summary of what candidate answered",\n'
            '      "score": 8,\n'
            '      "feedback": "Short summary of feedback"\n'
            '    }\n'
            '  ],\n'
            '  "recommended_preparation": ["Topic 1", "Topic 2", "Topic 3"]\n'
            "}\n"
            "Do not wrap in markdown quotes if possible, output pure JSON."
        )

        user_prompt = (
            f"INTERVIEW DETAILS:\n"
            f"Target Role: {role}\n"
            f"Base Difficulty: {difficulty}\n"
            f"Interview Type: {interview_type}\n\n"
            f"COMPLETE INTERVIEW TRANSCRIPT AND SCORES:\n"
            f"{full_transcript}\n\n"
            "Generate the comprehensive final interview report in JSON format."
        )

        response = openai_client.responses.create(
            model=cfg["model"],
            instructions=system_prompt,
            input=user_prompt
        )

        return parse_final_report_response(response.output_text)


_interview_service_instance: Optional[InterviewService] = None


def get_interview_service() -> InterviewService:
    global _interview_service_instance
    if _interview_service_instance is None:
        _interview_service_instance = InterviewService()
    return _interview_service_instance
