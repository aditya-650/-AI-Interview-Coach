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
        if tools:
            kwargs["tools"] = tools

        response = openai_client.responses.create(**kwargs)

        return response.output_text.strip()

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
        if tools:
            kwargs["tools"] = tools

        response = openai_client.responses.create(**kwargs)

        return {
            "question": response.output_text.strip(),
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
