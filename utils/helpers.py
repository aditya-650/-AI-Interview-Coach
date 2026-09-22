"""
utils/helpers.py
Helper functions, prompt builders, JSON/Markdown parsers, and validation utilities.
"""

import json
import re
from typing import Dict, Any, List, Optional


def clean_markdown_fences(raw_text: str) -> str:
    """Removes ```json and ``` code blocks if present."""
    if not raw_text:
        return ""
    text = raw_text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def parse_json_safely(raw_text: str, default: Any = None) -> Any:
    """Safely extracts and parses JSON from model output."""
    cleaned = clean_markdown_fences(raw_text)
    try:
        return json.loads(cleaned)
    except Exception:
        # Try finding the first JSON object or array with regex
        match = re.search(r'(\{.*\}|\[.*\])', raw_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception:
                pass
    return default


def parse_evaluation_response(raw_text: str) -> Dict[str, Any]:
    """
    Parses the answer evaluation response into structured dictionary.
    Handles both JSON structure and Markdown fallback.
    """
    parsed = parse_json_safely(raw_text)
    if isinstance(parsed, dict) and "score" in parsed:
        try:
            score = float(parsed.get("score", 7))
        except (ValueError, TypeError):
            score = 7.0
        return {
            "score": score,
            "what_well": parsed.get("what_well", []) if isinstance(parsed.get("what_well"), list) else [str(parsed.get("what_well", ""))],
            "what_improve": parsed.get("what_improve", []) if isinstance(parsed.get("what_improve"), list) else [str(parsed.get("what_improve", ""))],
            "brief_commentary": parsed.get("brief_commentary", ""),
            "raw_text": raw_text
        }

    # Fallback regex parsing if LLM returned formatted text instead of pure JSON
    score_match = re.search(r'Score:\s*(\d+(?:\.\d+)?)\s*/\s*10', raw_text, re.IGNORECASE)
    score = float(score_match.group(1)) if score_match else 7.0

    what_well = []
    what_improve = []

    well_match = re.search(r'What you did well:(.*?)(?:What could be improved:|$)', raw_text, re.DOTALL | re.IGNORECASE)
    if well_match:
        items = re.findall(r'[-*•]\s*(.+)', well_match.group(1))
        what_well = [item.strip() for item in items if item.strip()]

    improve_match = re.search(r'What could be improved:(.*?)(?:$)', raw_text, re.DOTALL | re.IGNORECASE)
    if improve_match:
        items = re.findall(r'[-*•]\s*(.+)', improve_match.group(1))
        what_improve = [item.strip() for item in items if item.strip()]

    if not what_well:
        what_well = ["Demonstrated fundamental understanding of the core concept."]
    if not what_improve:
        what_improve = ["Could expand further on specific technical edge cases and implementations."]

    return {
        "score": score,
        "what_well": what_well,
        "what_improve": what_improve,
        "brief_commentary": "",
        "raw_text": raw_text
    }


def parse_final_report_response(raw_text: str) -> Dict[str, Any]:
    """
    Parses the final report JSON response. If JSON parsing fails, provides structured fallback.
    """
    parsed = parse_json_safely(raw_text)
    if isinstance(parsed, dict) and "overall_score" in parsed:
        return parsed

    # Default structured fallback
    return {
        "overall_score": 75,
        "technical_knowledge": 75,
        "answer_quality": 75,
        "communication": 75,
        "strengths": [
            "Good foundational understanding of concepts.",
            "Clear communication and articulate phrasing."
        ],
        "areas_for_improvement": [
            "Provide more concrete real-world implementation details.",
            "Discuss algorithmic tradeoffs and performance considerations."
        ],
        "question_performance": [],
        "recommended_preparation": [
            "System Design & Architecture",
            "Core Algorithms and Data Structures",
            "Domain-specific Best Practices"
        ],
        "raw_markdown": raw_text
    }
