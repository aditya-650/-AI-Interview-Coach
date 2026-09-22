"""
test_integration.py
Full automated integration test validating the entire pipeline:
1. Document Upload & Vector Store Indexing in Microsoft Foundry
2. File Search Grounded Question Generation
3. Azure AI Speech STT (Speech-to-Text)
4. AI Answer Evaluation & Scoring
5. Adaptive Next Question
6. Comprehensive Final Report Generation
7. Vector Store Cleanup
"""

import sys
import io
import os
import tempfile
from dotenv import load_dotenv

load_dotenv()

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from services.foundry_service import get_foundry_service
from services.document_service import get_document_service
from services.speech_service import get_speech_service
from services.interview_service import get_interview_service
import azure.cognitiveservices.speech as speechsdk

print("=" * 60)
print("  Interview IQ - End-to-End Pipeline Verification")
print("=" * 60)

doc_service = get_document_service()
speech_service = get_speech_service()
interview_service = get_interview_service()

# Step 1: Upload mock resume document
print("\n[Step 1] Creating temporary document and uploading to Foundry Vector Store...")
mock_doc_content = b"""
Candidate Name: Alex Johnson
Title: Senior Machine Learning Engineer
Education: B.S. in Computer Science
Key Projects:
1. Distributed Fraud Detection Engine: Designed a low-latency fraud detection system using PyTorch, Kafka, and Redis. Reduced false positive alerts by 34% with an ensemble XGBoost model.
2. Multimodal Search Pipeline: Built vector search embeddings using OpenAI CLIP and Azure AI Search for an e-commerce catalog of 5M products.
Technical Skills: Python, PyTorch, Azure AI, Docker, Kubernetes, SQL, FastAPI, MLOps.
"""

class MockUploadedFile:
    def __init__(self, name, content):
        self.name = name
        self.content = content
        self.size = len(content)
    def read(self):
        return self.content
    def getvalue(self):
        return self.content

mock_file = MockUploadedFile("alex_johnson_resume.txt", mock_doc_content)
index_res = doc_service.process_and_index_document(mock_file)
vs_id = index_res["vector_store_id"]
file_id = index_res["file_id"]
print(f"  [OK] Ingested in Vector Store: {vs_id} (File: {file_id}, Status: {index_res['status']})")

try:
    # Step 2: Generate Question #1 grounded in resume
    print("\n[Step 2] Generating question grounded in resume via Foundry Agent...")
    q1 = interview_service.generate_first_question(
        role="AI/ML Engineer",
        difficulty="Medium",
        interview_type="Technical",
        vector_store_id=vs_id
    )
    print(f"  [OK] Question 1:\n  \"{q1}\"")

    # Step 3: Test Azure AI Speech with audio bytes
    print("\n[Step 3] Testing Azure AI Speech-to-Text transcription...")
    # Generate speech audio to simulate user speaking into mic
    speech_cfg = speechsdk.SpeechConfig(
        subscription=os.getenv("AZURE_SPEECH_KEY"),
        region=os.getenv("AZURE_SPEECH_REGION")
    )
    temp_wav_path = os.path.join(tempfile.gettempdir(), "simulated_answer.wav")
    audio_output = speechsdk.audio.AudioOutputConfig(filename=temp_wav_path)
    synth = speechsdk.SpeechSynthesizer(speech_config=speech_cfg, audio_config=audio_output)
    synth_text = "In my fraud detection project, we used an ensemble XGBoost model with Kafka streaming to process transactions in real time."
    synth.speak_text_async(synth_text).get()
    del synth
    del audio_output

    with open(temp_wav_path, "rb") as f:
        audio_bytes = f.read()
    try:
        os.remove(temp_wav_path)
    except Exception:
        pass

    transcript = speech_service.transcribe_audio_bytes(audio_bytes, "simulated_answer.wav")
    print(f"  [OK] Azure Speech Transcribed: \"{transcript}\"")

    # Step 4: Evaluate Candidate Answer
    print("\n[Step 4] Evaluating Answer with Microsoft Foundry...")
    eval_res = interview_service.evaluate_answer(
        question=q1,
        candidate_answer=transcript,
        role="AI/ML Engineer",
        difficulty="Medium",
        vector_store_id=vs_id
    )
    print(f"  [OK] Score: {eval_res['score']}/10")
    print(f"  What you did well: {eval_res['what_well']}")
    print(f"  What could be improved: {eval_res['what_improve']}")

    # Step 5: Adaptive Next Question
    print("\n[Step 5] Generating Adaptive Next Question...")
    history = [{
        "question_num": 1,
        "question": q1,
        "answer": transcript,
        "score": eval_res["score"],
        "what_well": eval_res["what_well"],
        "what_improve": eval_res["what_improve"]
    }]
    next_q = interview_service.generate_next_adaptive_question(
        role="AI/ML Engineer",
        current_difficulty="Medium",
        interview_type="Technical",
        history=history,
        question_index=2,
        total_questions=3,
        vector_store_id=vs_id
    )
    print(f"  [OK] Next Question (Difficulty: {next_q['new_difficulty']}):\n  \"{next_q['question']}\"")

    # Step 6: Generate Final Report
    print("\n[Step 6] Synthesizing Final Report...")
    report = interview_service.generate_final_report(
        role="AI/ML Engineer",
        difficulty="Medium",
        interview_type="Technical",
        history=history,
        vector_store_id=vs_id
    )
    print(f"  [OK] Overall Score: {report.get('overall_score')}/100")
    print(f"  Technical Knowledge: {report.get('technical_knowledge')}/100")
    print(f"  Strengths Count: {len(report.get('strengths', []))}")
    print(f"  Recommended Topics: {report.get('recommended_preparation', [])}")

finally:
    # Step 7: Clean up
    print("\n[Step 7] Cleaning up Foundry Vector Store...")
    doc_service.cleanup_vector_store(vs_id, file_id)
    print("  [OK] Vector Store cleaned up successfully.")

print("\n" + "=" * 60)
print("  ALL PIPELINE STEPS PASSED SUCCESSFULLY! ✅")
print("=" * 60)
