"""
app.py
Streamlit Application for Interview IQ - AI-Powered Interview Coach.
Built with Microsoft Azure AI Foundry, GPT-4.1-mini, File Search RAG, Azure AI Speech,
SQLite Authentication & Quiz History Tracking, and Ultra-Modern Cyberpunk / SaaS UI.
"""

import streamlit as st
import time
import html
from services.foundry_service import get_foundry_service
from services.document_service import get_document_service
from services.speech_service import get_speech_service
from services.interview_service import get_interview_service
from services.db_service import get_db_service

# -----------------------------------------------------------------------------
# PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Interview IQ - Frontier AI Interview Coach",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -----------------------------------------------------------------------------
# SERVICE INITIALIZATION
# -----------------------------------------------------------------------------
foundry_service = get_foundry_service()
doc_service = get_document_service()
speech_service = get_speech_service()
interview_service = get_interview_service()
db_service = get_db_service()

# -----------------------------------------------------------------------------
# SESSION STATE INITIALIZATION
# -----------------------------------------------------------------------------
if "current_view" not in st.session_state:
    st.session_state.current_view = "landing"  # "landing", "auth", "questions", "setup", "interviewing", "evaluated", "report"

if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "signin"  # "signin" or "signup"

if "user" not in st.session_state:
    st.session_state.user = None  # None when logged out, dict when logged in

if "stage" not in st.session_state:
    st.session_state.stage = "setup"

if "role" not in st.session_state:
    st.session_state.role = "AI/ML Engineer"

if "difficulty" not in st.session_state:
    st.session_state.difficulty = "Medium"

if "current_difficulty" not in st.session_state:
    st.session_state.current_difficulty = "Medium"

if "interview_type" not in st.session_state:
    st.session_state.interview_type = "Technical"

if "total_questions" not in st.session_state:
    st.session_state.total_questions = 5

if "current_question_index" not in st.session_state:
    st.session_state.current_question_index = 1

if "current_question" not in st.session_state:
    st.session_state.current_question = ""

if "candidate_answer" not in st.session_state:
    st.session_state.candidate_answer = ""

if "last_transcription" not in st.session_state:
    st.session_state.last_transcription = ""

if "last_evaluation" not in st.session_state:
    st.session_state.last_evaluation = None

if "history" not in st.session_state:
    st.session_state.history = []

if "vector_store_id" not in st.session_state:
    st.session_state.vector_store_id = None

if "file_id" not in st.session_state:
    st.session_state.file_id = None

if "file_name" not in st.session_state:
    st.session_state.file_name = None

if "final_report" not in st.session_state:
    st.session_state.final_report = None

if "_interview_saved_to_db" not in st.session_state:
    st.session_state._interview_saved_to_db = False

if "show_google_chooser" not in st.session_state:
    st.session_state.show_google_chooser = False

# -----------------------------------------------------------------------------
# ULTRA-PREMIUM CYBERPUNK / SAAS DESIGN SYSTEM CSS
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

    * {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        box-sizing: border-box;
    }

    /* Core Application Background */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #06080F !important;
        background-image: 
            radial-gradient(circle at 50% -10%, rgba(124, 58, 237, 0.2) 0%, transparent 50%),
            radial-gradient(circle at 90% 20%, rgba(6, 182, 212, 0.1) 0%, transparent 40%),
            radial-gradient(circle at 10% 80%, rgba(139, 92, 246, 0.08) 0%, transparent 40%) !important;
        color: #F8FAFC !important;
    }

    /* Hide standard Streamlit header decoration */
    header[data-testid="stHeader"] {
        background: transparent !important;
    }

    /* Top Nav Container */
    .nav-wrapper {
        border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        padding-bottom: 15px;
        margin-bottom: 30px;
    }
    .nav-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(124, 58, 237, 0.15);
        border: 1px solid rgba(139, 92, 246, 0.35);
        color: #A78BFA;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.05em;
    }
    .nav-badge-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background-color: #06B6D4;
        box-shadow: 0 0 8px #06B6D4;
    }
    .nav-brand {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        font-size: 1.35rem;
        font-weight: 800;
        color: #FFFFFF;
        letter-spacing: -0.02em;
    }
    .brand-icon {
        width: 32px;
        height: 32px;
        background: linear-gradient(135deg, #7C3AED 0%, #06B6D4 100%);
        border-radius: 8px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 1rem;
        box-shadow: 0 0 16px rgba(124, 58, 237, 0.5);
    }

    /* Nav Button Styling */
    div[data-testid="column"] button {
        background: transparent !important;
        border: none !important;
        color: #94A3B8 !important;
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        padding: 8px 16px !important;
        transition: all 0.2s ease !important;
    }
    div[data-testid="column"] button:hover {
        color: #FFFFFF !important;
        background: rgba(255, 255, 255, 0.08) !important;
        border-radius: 8px !important;
    }

    /* Hero Section */
    .hero-pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(6, 182, 212, 0.1);
        border: 1px solid rgba(6, 182, 212, 0.3);
        padding: 6px 16px;
        border-radius: 9999px;
        color: #38BDF8;
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 20px;
    }
    .hero-pill-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: #38BDF8;
        box-shadow: 0 0 8px #38BDF8;
    }
    .hero-title {
        font-size: 4.2rem;
        font-weight: 800;
        line-height: 1.1;
        letter-spacing: -0.03em;
        color: #FFFFFF;
        margin-bottom: 8px;
        text-align: center;
    }
    .hero-title-gradient {
        background: linear-gradient(135deg, #A855F7 0%, #6366F1 50%, #38BDF8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .hero-subtitle {
        font-size: 1.25rem;
        color: #94A3B8;
        max-width: 680px;
        margin: 18px auto 30px auto;
        text-align: center;
        line-height: 1.6;
    }
    .hero-value-props {
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 24px;
        flex-wrap: wrap;
        margin: 20px 0 35px 0;
        color: #64748B;
        font-size: 0.85rem;
    }
    .hero-prop-item {
        display: flex;
        align-items: center;
        gap: 6px;
        color: #94A3B8;
    }

    /* THE FUTURISTIC COCKPIT CARD */
    .cockpit-card {
        background: #0B0F1D;
        border: 1px solid rgba(139, 92, 246, 0.35);
        border-radius: 24px;
        padding: 32px;
        margin: 20px auto;
        box-shadow: 
            0 0 70px -15px rgba(124, 58, 237, 0.4),
            0 25px 50px -12px rgba(0, 0, 0, 0.8);
        position: relative;
        overflow: hidden;
    }
    .cockpit-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, #8B5CF6, #06B6D4, transparent);
    }
    .cockpit-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-bottom: 24px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        flex-wrap: wrap;
        gap: 15px;
    }
    .interviewer-info {
        display: flex;
        align-items: center;
        gap: 14px;
    }
    .interviewer-avatar {
        width: 44px;
        height: 44px;
        border-radius: 12px;
        background: linear-gradient(135deg, #4F46E5 0%, #06B6D4 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.3rem;
        box-shadow: 0 0 15px rgba(99, 102, 241, 0.5);
    }
    .interviewer-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: #FFFFFF;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .master-badge {
        font-size: 0.7rem;
        background: rgba(139, 92, 246, 0.2);
        border: 1px solid rgba(139, 92, 246, 0.4);
        color: #C4B5FD;
        padding: 2px 8px;
        border-radius: 6px;
        font-weight: 600;
    }
    .interviewer-sub {
        font-size: 0.82rem;
        color: #94A3B8;
    }
    .telemetry-chip {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.3);
        color: #34D399;
        padding: 5px 12px;
        border-radius: 8px;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.06em;
    }
    .chip-pulse {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background-color: #10B981;
        box-shadow: 0 0 8px #10B981;
    }

    /* Question Box inside Cockpit */
    .cockpit-prompt-box {
        background: #11172A;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 28px;
        margin: 24px 0;
    }
    .prompt-tag {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #38BDF8;
        margin-bottom: 14px;
    }
    .prompt-tag-icon {
        background: rgba(56, 189, 248, 0.2);
        border: 1px solid rgba(56, 189, 248, 0.4);
        color: #38BDF8;
        width: 22px;
        height: 22px;
        border-radius: 6px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.7rem;
    }
    .prompt-text {
        font-size: 1.3rem;
        font-weight: 600;
        line-height: 1.6;
        color: #F8FAFC;
        margin: 0;
    }

    /* Central Voice / Mic Visualizer */
    .mic-center-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 25px 0 15px 0;
    }
    .glowing-mic-btn {
        width: 76px;
        height: 76px;
        border-radius: 50%;
        background: linear-gradient(135deg, #7C3AED 0%, #06B6D4 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.8rem;
        color: #FFFFFF;
        box-shadow: 0 0 35px rgba(6, 182, 212, 0.55), 0 0 60px rgba(124, 58, 237, 0.35);
        margin-bottom: 16px;
    }
    .ai-status-pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(99, 102, 241, 0.12);
        border: 1px solid rgba(99, 102, 241, 0.3);
        padding: 6px 18px;
        border-radius: 9999px;
        font-size: 0.82rem;
        font-weight: 600;
        color: #A5B4FC;
        margin-bottom: 18px;
    }
    .soundwave-container {
        display: flex;
        align-items: center;
        gap: 4px;
        height: 36px;
        margin-bottom: 24px;
    }
    .soundwave-bar {
        width: 4px;
        border-radius: 9999px;
        background: linear-gradient(180deg, #38BDF8 0%, #6366F1 100%);
        animation: soundWave 1.2s ease-in-out infinite alternate;
    }
    .soundwave-bar:nth-child(1) { height: 10px; animation-delay: 0.1s; }
    .soundwave-bar:nth-child(2) { height: 18px; animation-delay: 0.3s; }
    .soundwave-bar:nth-child(3) { height: 32px; animation-delay: 0.5s; }
    .soundwave-bar:nth-child(4) { height: 24px; animation-delay: 0.2s; }
    .soundwave-bar:nth-child(5) { height: 36px; animation-delay: 0.6s; }
    .soundwave-bar:nth-child(6) { height: 28px; animation-delay: 0.4s; }
    .soundwave-bar:nth-child(7) { height: 14px; animation-delay: 0.1s; }
    .soundwave-bar:nth-child(8) { height: 22px; animation-delay: 0.3s; }

    @keyframes soundWave {
        0% { transform: scaleY(0.4); }
        100% { transform: scaleY(1.3); }
    }

    /* Telemetry HUD Cards */
    .telemetry-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 16px;
        margin: 20px 0;
    }
    .telemetry-card {
        background: #11172A;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 16px 20px;
    }
    .telemetry-card-top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
    }
    .telemetry-card-title {
        font-size: 0.85rem;
        font-weight: 700;
        color: #E2E8F0;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .telemetry-card-score {
        font-size: 0.9rem;
        font-weight: 800;
        color: #38BDF8;
    }
    .telemetry-metric-sub {
        display: flex;
        justify-content: space-between;
        font-size: 0.78rem;
        color: #94A3B8;
        padding-top: 8px;
        border-top: 1px solid rgba(255, 255, 255, 0.05);
    }

    /* DEDICATED AUTH CARD (MATCHING media_1790053572685.png) */
    .auth-page-container {
        max-width: 480px;
        margin: 20px auto 60px auto;
    }
    .auth-card-exact {
        background: #0D1322;
        border: 1px solid rgba(139, 92, 246, 0.25);
        border-radius: 24px;
        padding: 38px 32px;
        box-shadow: 
            0 0 60px -15px rgba(124, 58, 237, 0.35),
            0 25px 50px -12px rgba(0, 0, 0, 0.9);
        text-align: center;
    }
    .auth-center-icon {
        width: 52px;
        height: 52px;
        border-radius: 16px;
        background: rgba(124, 58, 237, 0.2);
        border: 1px solid rgba(139, 92, 246, 0.4);
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        color: #A78BFA;
        margin-bottom: 18px;
    }
    .auth-title {
        font-size: 2rem;
        font-weight: 800;
        color: #FFFFFF;
        margin-bottom: 6px;
        letter-spacing: -0.02em;
    }
    .auth-sub {
        font-size: 0.95rem;
        color: #94A3B8;
        margin-bottom: 26px;
    }
    .social-btn-row {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 12px;
        margin-bottom: 24px;
    }
    .auth-divider {
        display: flex;
        align-items: center;
        color: #64748B;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin: 20px 0 24px 0;
    }
    .auth-divider::before, .auth-divider::after {
        content: '';
        flex: 1;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }
    .auth-divider span {
        padding: 0 12px;
    }
    .auth-success-banner {
        background: rgba(16, 185, 129, 0.12);
        border: 1px solid rgba(16, 185, 129, 0.35);
        color: #34D399;
        border-radius: 12px;
        padding: 12px 16px;
        font-size: 0.85rem;
        text-align: left;
        margin-bottom: 20px;
    }

    /* GOOGLE ACCOUNT CHOOSER MODAL STYLES */
    div[data-testid="stDialog"] div[role="dialog"] {
        background: #0B1120 !important;
        border: 1px solid rgba(255, 255, 255, 0.14) !important;
        border-radius: 20px !important;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.95), 0 0 40px rgba(66, 133, 244, 0.25) !important;
    }
    .google-acc-card {
        display: flex;
        align-items: center;
        gap: 14px;
        padding: 12px 14px;
        border-radius: 14px;
        border: 1px solid rgba(255, 255, 255, 0.09);
        background: rgba(255, 255, 255, 0.03);
        margin-bottom: 8px;
    }
    .google-acc-avatar {
        width: 42px;
        height: 42px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 15px;
        color: #FFFFFF;
        flex-shrink: 0;
    }
    .google-acc-info {
        flex-grow: 1;
        overflow: hidden;
    }
    .google-acc-name {
        font-weight: 700;
        color: #F8FAFC;
        font-size: 0.96rem;
        line-height: 1.2;
    }
    .google-acc-email {
        color: #94A3B8;
        font-size: 0.82rem;
        margin-top: 3px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    /* Role Pills */
    .role-pills-row {
        display: flex;
        justify-content: center;
        gap: 12px;
        flex-wrap: wrap;
        margin: 30px 0 50px 0;
    }
    .role-pill-item {
        background: #0E1424;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 9999px;
        padding: 6px 16px;
        font-size: 0.82rem;
        color: #94A3B8;
        font-weight: 600;
    }
    .role-pill-item span {
        color: #38BDF8;
        margin-right: 4px;
    }

    /* Feature Grid Section */
    .feature-section {
        margin: 70px 0;
        text-align: center;
    }
    .feature-header-tag {
        color: #38BDF8;
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin-bottom: 10px;
    }
    .feature-main-title {
        font-size: 2.3rem;
        font-weight: 800;
        color: #FFFFFF;
        letter-spacing: -0.02em;
        margin-bottom: 45px;
    }
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 20px;
    }
    .feature-card {
        background: #0D1224;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 28px 22px;
        text-align: left;
        transition: all 0.25s ease;
    }
    .feature-card:hover {
        border-color: rgba(139, 92, 246, 0.4);
        transform: translateY(-3px);
        box-shadow: 0 10px 30px -10px rgba(124, 58, 237, 0.3);
    }
    .feature-icon-circle {
        width: 44px;
        height: 44px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
        margin-bottom: 20px;
    }
    .icon-cyan { background: rgba(6, 182, 212, 0.15); color: #22D3EE; border: 1px solid rgba(6, 182, 212, 0.3); }
    .icon-purple { background: rgba(139, 92, 246, 0.15); color: #C084FC; border: 1px solid rgba(139, 92, 246, 0.3); }
    .icon-blue { background: rgba(59, 130, 246, 0.15); color: #60A5FA; border: 1px solid rgba(59, 130, 246, 0.3); }
    .icon-green { background: rgba(16, 185, 129, 0.15); color: #34D399; border: 1px solid rgba(16, 185, 129, 0.3); }
    .feature-num {
        font-size: 0.75rem;
        font-weight: 700;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 6px;
    }
    .feature-card-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: #F8FAFC;
        margin-bottom: 10px;
    }
    .feature-card-desc {
        font-size: 0.85rem;
        color: #94A3B8;
        line-height: 1.55;
    }

    /* Bottom CTA Card */
    .bottom-cta-card {
        background: linear-gradient(135deg, #0E1428 0%, #151A36 100%);
        border: 1px solid rgba(139, 92, 246, 0.35);
        border-radius: 20px;
        padding: 50px 30px;
        text-align: center;
        margin: 60px 0 40px 0;
        box-shadow: 0 10px 40px -10px rgba(124, 58, 237, 0.25);
    }

    /* Footer */
    .app-footer {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 25px 0;
        border-top: 1px solid rgba(255, 255, 255, 0.06);
        color: #64748B;
        font-size: 0.82rem;
        flex-wrap: wrap;
        gap: 15px;
    }
    .footer-links {
        display: flex;
        gap: 20px;
    }

    /* Streamlit Control Overrides */
    .stTextInput input, .stTextArea textarea {
        background-color: #0E1424 !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 12px !important;
        color: #F8FAFC !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #8B5CF6 !important;
        box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.3) !important;
    }
    .stSelectbox [data-baseweb="select"] {
        background-color: #0E1424 !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 12px !important;
        color: #F8FAFC !important;
    }
    .stButton button[kind="primary"] {
        background: linear-gradient(135deg, #7C3AED 0%, #06B6D4 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        padding: 12px 24px !important;
        box-shadow: 0 4px 20px rgba(6, 182, 212, 0.4) !important;
        transition: all 0.2s ease !important;
    }
    .stButton button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 25px rgba(124, 58, 237, 0.5) !important;
    }
    .stButton button[kind="secondary"] {
        background: #11172A !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        color: #E2E8F0 !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
    }
    .stButton button[kind="secondary"]:hover {
        border-color: #8B5CF6 !important;
        background: #18223D !important;
    }
    [data-testid="stExpander"] {
        background-color: #0D1326 !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 14px !important;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# HELPER ACTIONS
# -----------------------------------------------------------------------------
def reset_interview():
    """Cleans up vector store and resets state for a new interview session."""
    if st.session_state.vector_store_id:
        doc_service.cleanup_vector_store(
            st.session_state.vector_store_id,
            st.session_state.file_id
        )
    st.session_state.stage = "setup"
    st.session_state.current_question_index = 1
    st.session_state.current_question = ""
    st.session_state.candidate_answer = ""
    st.session_state.last_transcription = ""
    st.session_state.last_evaluation = None
    st.session_state.history = []
    st.session_state.vector_store_id = None
    st.session_state.file_id = None
    st.session_state.file_name = None
    st.session_state.final_report = None
    st.session_state._interview_saved_to_db = False
    st.session_state._last_seen_audio_bytes = None
    for k in list(st.session_state.keys()):
        if k.startswith("answer_text_area_") or k.startswith("audio_input_q_"):
            del st.session_state[k]


def logout_user():
    """Logs out current user and returns to landing page."""
    reset_interview()
    st.session_state.user = None
    st.session_state.current_view = "landing"
    st.rerun()


# -----------------------------------------------------------------------------
# GOOGLE ACCOUNT CHOOSER DIALOG (NATIVE OAUTH MODAL)
# -----------------------------------------------------------------------------
def dismiss_google_dialog():
    st.session_state.show_google_chooser = False


@st.dialog("Sign in with Google", width="small", on_dismiss=dismiss_google_dialog)
def google_account_chooser_dialog():
    # Google standard branding
    st.markdown("""
    <div style="text-align: center; margin-bottom: 20px;">
        <svg viewBox="0 0 48 48" width="40px" height="40px" style="display: block; margin: 0 auto 10px auto;">
            <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
            <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
            <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
            <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
            <path fill="none" d="M0 0h48v48H0z"/>
        </svg>
        <div style="font-size: 1.35rem; font-weight: 700; color: #FFFFFF; letter-spacing: -0.01em;">Choose an account</div>
        <div style="font-size: 0.9rem; color: #94A3B8; margin-top: 4px;">to continue to <span style="font-weight: 600; color: #38BDF8;">Interview IQ</span></div>
    </div>
    """, unsafe_allow_html=True)

    # Account 1: Aditya Sharma
    st.markdown("""
    <div class="google-acc-card">
        <div class="google-acc-avatar" style="background: linear-gradient(135deg, #3B82F6, #1D4ED8); box-shadow: 0 2px 10px rgba(59, 130, 246, 0.4);">
            AS
        </div>
        <div class="google-acc-info">
            <div class="google-acc-name">Aditya Sharma</div>
            <div class="google-acc-email">aditya.interview@gmail.com</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Continue as Aditya Sharma", key="btn_g_acc_1", use_container_width=True, type="primary"):
        user_data = db_service.get_or_create_oauth_user("Aditya Sharma", "aditya.interview@gmail.com")
        st.session_state.user = user_data
        st.session_state.show_google_chooser = False
        st.session_state.current_view = "setup"
        st.rerun()

    st.write("")

    # Account 2: Aditya (Tech / College)
    st.markdown("""
    <div class="google-acc-card">
        <div class="google-acc-avatar" style="background: linear-gradient(135deg, #10B981, #059669); box-shadow: 0 2px 10px rgba(16, 185, 129, 0.4);">
            AW
        </div>
        <div class="google-acc-info">
            <div class="google-acc-name">Aditya (Work & College)</div>
            <div class="google-acc-email">aditya65011pkl@outlook.com</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Continue as Aditya (Work)", key="btn_g_acc_2", use_container_width=True):
        user_data = db_service.get_or_create_oauth_user("Aditya (Work)", "aditya65011pkl@outlook.com")
        st.session_state.user = user_data
        st.session_state.show_google_chooser = False
        st.session_state.current_view = "setup"
        st.rerun()

    st.write("")

    # Account 3: Use another account
    with st.expander("➕ Use another Google account", expanded=False):
        with st.form("custom_google_account_form", clear_on_submit=False):
            st.markdown("<div style='font-size: 0.85rem; color: #94A3B8; margin-bottom: 8px;'>Enter your Google profile information:</div>", unsafe_allow_html=True)
            cust_name = st.text_input("Full Name", placeholder="e.g. Aditya", key="g_cust_name")
            cust_email = st.text_input("Google Email Address", placeholder="e.g. aditya@gmail.com", key="g_cust_email")
            btn_cust = st.form_submit_button("Continue with this account ➜", type="primary", use_container_width=True)
            if btn_cust:
                if not cust_name or not cust_email or "@" not in cust_email:
                    st.error("Please enter a valid full name and Google email address.")
                else:
                    user_data = db_service.get_or_create_oauth_user(cust_name.strip(), cust_email.strip())
                    st.session_state.user = user_data
                    st.session_state.show_google_chooser = False
                    st.session_state.current_view = "setup"
                    st.rerun()

    # Footer notice & Cancel button
    st.markdown("""
    <div style="font-size: 0.74rem; color: #64748B; margin-top: 18px; line-height: 1.45; text-align: center; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 12px;">
        To continue, Google will share your name, email address, language preference, and profile picture with <b>Interview IQ</b>. See Interview IQ's <span style="color: #38BDF8;">Privacy Policy</span> and <span style="color: #38BDF8;">Terms of Service</span>.
    </div>
    """, unsafe_allow_html=True)

    col_c1, col_c2 = st.columns([1, 1])
    with col_c1:
        if st.button("Cancel", key="btn_g_cancel", use_container_width=True):
            st.session_state.show_google_chooser = False
            st.rerun()


# -----------------------------------------------------------------------------
# INTERACTIVE TOP NAVIGATION BAR (WITH FUNCTIONAL TOP-RIGHT AUTH)
# -----------------------------------------------------------------------------
st.markdown('<div class="nav-wrapper">', unsafe_allow_html=True)

nav_col1, nav_col2, nav_col3 = st.columns([1.5, 1.2, 2.5])

with nav_col1:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 12px; margin-top: 5px;">
        <span class="nav-badge"><span class="nav-badge-dot"></span> V3.5 LIVE</span>
        <div class="nav-brand">
            <div class="brand-icon">🎯</div>
            <span>Interview IQ</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with nav_col3:
    # Functional Top-Right Buttons
    if st.session_state.user is None:
        btn_c1, btn_c2, btn_c3, btn_c4 = st.columns([1, 1, 1, 1.1])
        with btn_c1:
            if st.button("Practice", key="nav_practice"):
                st.session_state.current_view = "setup" if st.session_state.user else "auth"
                st.session_state.auth_mode = "signin"
                st.rerun()
        with btn_c2:
            if st.button("Questions", key="nav_questions"):
                st.session_state.current_view = "questions"
                st.rerun()
        with btn_c3:
            if st.button("Sign In", key="nav_signin"):
                st.session_state.current_view = "auth"
                st.session_state.auth_mode = "signin"
                st.rerun()
        with btn_c4:
            if st.button("✨ Sign Up", key="nav_signup"):
                st.session_state.current_view = "auth"
                st.session_state.auth_mode = "signup"
                st.rerun()
    else:
        btn_c1, btn_c2, btn_c3, btn_c4 = st.columns([1, 1, 1.4, 1])
        with btn_c1:
            if st.button("Practice", key="nav_practice_logged"):
                st.session_state.current_view = "setup"
                st.rerun()
        with btn_c2:
            if st.button("Questions", key="nav_questions_logged"):
                st.session_state.current_view = "questions"
                st.rerun()
        with btn_c3:
            u_name = st.session_state.user["username"]
            st.markdown(f"<div style='margin-top: 8px; font-weight: 700; color: #38BDF8;'>👤 {u_name}</div>", unsafe_allow_html=True)
        with btn_c4:
            if st.button("Sign Out", key="nav_signout"):
                logout_user()

st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# GOOGLE ACCOUNT CHOOSER DIALOG TRIGGER
# -----------------------------------------------------------------------------
if st.session_state.get("show_google_chooser", False):
    google_account_chooser_dialog()


# =============================================================================
# VIEW 1: AUTHENTICATION SCREEN (EXACT MATCH OF media_1790053572685.png)
# =============================================================================
if st.session_state.current_view == "auth":

    # Top Sub-bar: Back to overview + Secure session
    sub_c1, sub_c2 = st.columns([1, 1])
    with sub_c1:
        if st.button("← Back to overview", key="btn_back_overview"):
            st.session_state.current_view = "landing"
            st.rerun()
    with sub_c2:
        st.markdown("<div style='text-align: right; color: #34D399; font-size: 0.85rem; font-weight: 700; margin-top: 8px;'>● Secure session</div>", unsafe_allow_html=True)

    st.write("")

    # Centered Auth Card Container
    col_l, col_center, col_r = st.columns([1, 1.6, 1])
    with col_center:
        st.markdown('<div class="auth-card-exact">', unsafe_allow_html=True)

        # Center Glowing Icon
        st.markdown("""
        <div class="auth-center-icon">✨</div>
        """, unsafe_allow_html=True)

        if st.session_state.auth_mode == "signin":
            st.markdown("""
            <div class="auth-title">Welcome back</div>
            <div class="auth-sub">Sign in to continue your interview practice</div>
            """, unsafe_allow_html=True)

            if st.session_state.get("_signup_success_msg"):
                st.markdown(f"""
                <div class="auth-success-banner">
                    ✔ <b>Account created successfully!</b><br>Please enter your credentials to sign in and begin.
                </div>
                """, unsafe_allow_html=True)
                st.session_state._signup_success_msg = False

            # One-Click Social Sign In
            st.markdown('<div class="social-btn-row">', unsafe_allow_html=True)
            col_g, col_gh = st.columns(2)
            with col_g:
                if st.button("🌐 Google", key="btn_google_auth", use_container_width=True):
                    st.session_state.show_google_chooser = True
                    st.rerun()
            with col_gh:
                if st.button("🐙 GitHub", key="btn_github_auth", use_container_width=True):
                    user_data = db_service.get_or_create_oauth_user("Aditya (GitHub)", "aditya.dev@github.com")
                    st.session_state.user = user_data
                    st.session_state.current_view = "setup"
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="auth-divider"><span>OR CONTINUE WITH EMAIL</span></div>', unsafe_allow_html=True)

            with st.form("signin_form_exact", clear_on_submit=False):
                email_input = st.text_input("Email address or Username", placeholder="e.g. alex.rivera@techcorp.io", key="auth_email")
                pass_input = st.text_input("Password", type="password", placeholder="••••••••••••", key="auth_pw")
                remember = st.checkbox("Remember me", value=True)
                submit_sign = st.form_submit_button("Sign In ➜", type="primary", use_container_width=True)

                if submit_sign:
                    if not email_input or not pass_input:
                        st.warning("Please enter your credentials.")
                    else:
                        ok, msg, user_data = db_service.authenticate_user(email_input, pass_input)
                        if ok:
                            st.session_state.user = user_data
                            st.session_state.current_view = "setup"
                            st.rerun()
                        else:
                            st.error(msg)

            st.write("")
            st.markdown("<div style='font-size: 0.88rem; color: #94A3B8;'>Don't have an account?</div>", unsafe_allow_html=True)
            if st.button("Sign up for free ✨", key="switch_to_signup"):
                st.session_state.auth_mode = "signup"
                st.rerun()

        else:
            # SIGN UP VIEW
            st.markdown("""
            <div class="auth-title">Create account</div>
            <div class="auth-sub">Register to build authentic interview command</div>
            """, unsafe_allow_html=True)

            # One-Click Social Sign Up
            st.markdown('<div class="social-btn-row">', unsafe_allow_html=True)
            col_g_su, col_gh_su = st.columns(2)
            with col_g_su:
                if st.button("🌐 Google", key="btn_google_auth_su", use_container_width=True):
                    st.session_state.show_google_chooser = True
                    st.rerun()
            with col_gh_su:
                if st.button("🐙 GitHub", key="btn_github_auth_su", use_container_width=True):
                    user_data = db_service.get_or_create_oauth_user("Aditya (GitHub)", "aditya.dev@github.com")
                    st.session_state.user = user_data
                    st.session_state.current_view = "setup"
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="auth-divider"><span>OR REGISTER WITH EMAIL</span></div>', unsafe_allow_html=True)

            with st.form("signup_form_exact", clear_on_submit=False):
                new_username = st.text_input("Choose Username", placeholder="e.g. alex_rivera", key="su_username")
                new_email = st.text_input("Email address", placeholder="alex.rivera@techcorp.io", key="su_email")
                new_pw = st.text_input("Create Password", type="password", placeholder="At least 6 characters", key="su_pw")
                confirm_pw = st.text_input("Confirm Password", type="password", placeholder="Repeat password", key="su_pw_confirm")
                submit_create = st.form_submit_button("Create Account ➜", type="primary", use_container_width=True)

                if submit_create:
                    if new_pw != confirm_pw:
                        st.error("Passwords do not match.")
                    else:
                        ok, msg, user_data = db_service.register_user(new_username, new_email, new_pw)
                        if ok:
                            st.session_state._signup_success_msg = True
                            st.session_state.auth_mode = "signin"
                            st.rerun()
                        else:
                            st.error(msg)

            st.write("")
            st.markdown("<div style='font-size: 0.88rem; color: #94A3B8;'>Already have an account?</div>", unsafe_allow_html=True)
            if st.button("Sign in here ➜", key="switch_to_signin"):
                st.session_state.auth_mode = "signin"
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    # Footer
    st.markdown("""
    <div class="app-footer" style="margin-top: 60px;">
        <div>⚡ © 2026 Interview IQ. Precision Cognitive Intelligence.</div>
        <div class="footer-links">
            <span>Privacy</span>
            <span>Terms</span>
            <span>Status</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.stop()


# =============================================================================
# VIEW 2: QUESTIONS BANK (ACCESSIBLE FROM TOP NAV "QUESTIONS")
# =============================================================================
elif st.session_state.current_view == "questions":

    sub_c1, sub_c2 = st.columns([1, 1])
    with sub_c1:
        if st.button("← Back to overview", key="btn_back_overview_q"):
            st.session_state.current_view = "landing"
            st.rerun()

    st.markdown("""
    <div style="margin: 20px 0 35px 0;">
        <div class="hero-pill">CURATED BENCHMARK PROMPTS</div>
        <div style="font-size: 2.8rem; font-weight: 800; color: #FFFFFF;">
            Explore Tier-1 Question Tracks
        </div>
        <div style="color: #94A3B8; font-size: 1.1rem; max-width: 650px;">
            Select a verified technical prompt to immediately launch a targeted practice session with our Microsoft Foundry Agent.
        </div>
    </div>
    """, unsafe_allow_html=True)

    q_tracks = [
        {
            "category": "Distributed Systems",
            "prompt": "Walk me through how you would architect a distributed real-time rate limiter handling 100k requests/sec with Redis and the Token Bucket algorithm.",
            "difficulty": "Hard",
            "role": "Distributed Systems Architect"
        },
        {
            "category": "Staff Machine Learning",
            "prompt": "How do you scale a low-latency vector similarity search indexing pipeline serving 50M embeddings with sub-15ms p99 retrieval?",
            "difficulty": "Hard",
            "role": "AI/ML Engineer"
        },
        {
            "category": "Core Infrastructure",
            "prompt": "Design a multi-region active-active Kubernetes failover architecture with automated health probes and cross-cluster service discovery.",
            "difficulty": "Hard",
            "role": "Software Engineer"
        },
        {
            "category": "Autonomous Agents & LLMs",
            "prompt": "Explain the architectural trade-offs between ReAct agent loops, hierarchical planner agents, and deterministic finite-state tool routing in production.",
            "difficulty": "Medium",
            "role": "AI/ML Engineer"
        }
    ]

    for idx, qt in enumerate(q_tracks):
        st.markdown(f"""
        <div class="cockpit-card" style="padding: 24px; margin-bottom: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <span class="prompt-tag"><span class="prompt-tag-icon">⚡</span> {qt['category']} • {qt['difficulty']}</span>
                <span style="font-size: 0.85rem; color: #94A3B8;">Target Role: <b>{qt['role']}</b></span>
            </div>
            <div style="font-size: 1.25rem; font-weight: 600; color: #FFFFFF; line-height: 1.5; margin-bottom: 18px;">
                "{qt['prompt']}"
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button(f"Practice This Prompt ➜", key=f"btn_practice_q_{idx}", type="primary"):
            st.session_state.role = qt['role']
            st.session_state.current_difficulty = qt['difficulty']
            st.session_state.difficulty = qt['difficulty']
            st.session_state.current_question = qt['prompt']
            st.session_state.current_question_index = 1
            st.session_state.total_questions = 5
            st.session_state.history = []
            st.session_state.candidate_answer = ""
            st.session_state.stage = "interviewing"
            st.session_state.current_view = "interviewing"
            st.rerun()

    st.stop()


# =============================================================================
# VIEW 3: MAIN LANDING PAGE (HERO + INTERACTIVE PREVIEW + FEATURE GRID)
# =============================================================================
elif st.session_state.current_view == "landing":

    # HERO SECTION
    st.markdown("""
    <div style="text-align: center; margin-top: 10px;">
        <div class="hero-pill">
            <span class="hero-pill-dot"></span>
            SUB-150MS DUPLEX SPEECH ENGINE • TRY INTERACTIVE LOOP &gt;
        </div>
        <div class="hero-title">
            Practice smarter.<br>
            <span class="hero-title-gradient">Interview better.</span>
        </div>
        <div class="hero-subtitle">
            Simulate authentic voice interviews with frontier AI models, receive instant rubric-level telemetry, and build the command to conquer the loop.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # HERO CALL TO ACTIONS (FUNCTIONAL BUTTONS)
    col_btn_l, col_btn_c, col_btn_r = st.columns([1, 1.8, 1])
    with col_btn_c:
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            # CLICKABLE: LEADS DIRECTLY TO AUTH / PRACTICE SETUP
            if st.button("Start Free Mock Interview ➜", key="hero_start_btn", type="primary", use_container_width=True):
                if st.session_state.user:
                    st.session_state.current_view = "setup"
                else:
                    st.session_state.current_view = "auth"
                    st.session_state.auth_mode = "signin"
                st.rerun()

        with col_b2:
            # CLICKABLE: QUICK DEMO LAUNCH
            if st.button("⚡ Watch Interactive Demo", key="hero_demo_btn", type="secondary", use_container_width=True):
                db_service.register_user("demo_user", "demo@interviewiq.ai", "password123")
                ok, msg, user_data = db_service.authenticate_user("demo_user", "password123")
                if ok:
                    st.session_state.user = user_data
                    st.session_state.role = "AI/ML Engineer"
                    st.session_state.difficulty = "Hard"
                    st.session_state.current_difficulty = "Hard"
                    st.session_state.current_question = "Walk me through how you would architect a distributed real-time rate limiter handling 100k requests/sec with Redis and the Token Bucket algorithm."
                    st.session_state.current_question_index = 1
                    st.session_state.total_questions = 5
                    st.session_state.history = []
                    st.session_state.stage = "interviewing"
                    st.session_state.current_view = "interviewing"
                    st.rerun()

    st.markdown("""
    <div class="hero-value-props">
        <span class="hero-prop-item">✔ zero credit card required</span>
        <span>•</span>
        <span class="hero-prop-item">✔ natural duplex voice interruption</span>
        <span>•</span>
        <span class="hero-prop-item">✔ 50ms voice roundtrip</span>
    </div>
    """, unsafe_allow_html=True)

    st.write("")

    # INTERACTIVE TERMINAL PREVIEW (THE COCKPIT CARD FROM MOCKUP)
    st.markdown("""
    <div class="cockpit-card">
        <div class="cockpit-header">
            <div class="interviewer-info">
                <div class="interviewer-avatar">🤖</div>
                <div>
                    <div class="interviewer-title">
                        AI Staff Principal Interviewer 
                        <span class="master-badge">Master</span>
                    </div>
                    <div class="interviewer-sub">System Architecture & Technical Depth</div>
                </div>
            </div>
            <div style="display: flex; align-items: center; gap: 16px;">
                <span style="font-size: 0.85rem; font-weight: 700; color: #818CF8;">Prompt 02 / 05</span>
                <span class="telemetry-chip"><span class="chip-pulse"></span> LIVE DUPLEX 100 FPS</span>
            </div>
        </div>
        <div class="cockpit-prompt-box">
            <div class="prompt-tag">
                <span class="prompt-tag-icon">⚡</span>
                ACTIVE TECHNICAL PROMPT • Hard • Distributed Systems
            </div>
            <p class="prompt-text">
                "Walk me through how you would architect a distributed real-time rate limiter handling 100k requests/sec with Redis and the Token Bucket algorithm."
            </p>
        </div>
        <div class="mic-center-container">
            <div class="glowing-mic-btn">🎙️</div>
            <div class="ai-status-pill">● AI Analyzing Concurrency Trade-offs & Structure...</div>
            <div class="soundwave-container">
                <div class="soundwave-bar"></div>
                <div class="soundwave-bar"></div>
                <div class="soundwave-bar"></div>
                <div class="soundwave-bar"></div>
                <div class="soundwave-bar"></div>
                <div class="soundwave-bar"></div>
                <div class="soundwave-bar"></div>
                <div class="soundwave-bar"></div>
            </div>
        </div>
        <div class="telemetry-grid">
            <div class="telemetry-card">
                <div class="telemetry-card-top">
                    <span class="telemetry-card-title">📊 Technical Rigor</span>
                    <span class="telemetry-card-score">100% +4</span>
                </div>
                <div class="telemetry-metric-sub">
                    <span>Scalability: Exceptional</span>
                    <span>Edge Cases: Evaluated</span>
                </div>
            </div>
            <div class="telemetry-card">
                <div class="telemetry-card-top">
                    <span class="telemetry-card-title">🗣️ Executive Delivery</span>
                    <span class="telemetry-card-score">92% +1.2</span>
                </div>
                <div class="telemetry-metric-sub">
                    <span>Framework: STAR-Aligned</span>
                    <span>Conciseness: 145 WPM</span>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ROLE PILLS ROW (FUNCTIONAL FILTER/SELECTION)
    st.markdown("""
    <div style="text-align: center; margin: 40px 0 15px 0; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.1em; color: #64748B; text-transform: uppercase;">
        ENGINEERS & LEADERS PREPARING FOR INTERVIEWS AT FORWARD-THINKING COMPANIES
    </div>
    """, unsafe_allow_html=True)

    col_p1, col_p2, col_p3, col_p4, col_p5 = st.columns(5)
    with col_p1:
        if st.button("#01 Distributed Systems", key="pill_dist"):
            st.session_state.role = "Distributed Systems Architect"
            st.session_state.current_view = "setup" if st.session_state.user else "auth"
            st.rerun()
    with col_p2:
        if st.button("#02 Staff Machine Learning", key="pill_ml"):
            st.session_state.role = "AI/ML Engineer"
            st.session_state.current_view = "setup" if st.session_state.user else "auth"
            st.rerun()
    with col_p3:
        if st.button("#03 Core Infrastructure", key="pill_infra"):
            st.session_state.role = "Software Engineer"
            st.session_state.current_view = "setup" if st.session_state.user else "auth"
            st.rerun()
    with col_p4:
        if st.button("#04 Autonomous Agents", key="pill_agents"):
            st.session_state.role = "AI/ML Engineer"
            st.session_state.current_view = "setup" if st.session_state.user else "auth"
            st.rerun()
    with col_p5:
        if st.button("#05 Quantitative Systems", key="pill_hft"):
            st.session_state.role = "Python Developer"
            st.session_state.current_view = "setup" if st.session_state.user else "auth"
            st.rerun()

    # "ENGINEERED FOR EXCELLENCE" FEATURE GRID (FROM MOCKUP)
    st.markdown("""
    <div class="feature-section">
        <div class="feature-header-tag">ENGINEERED FOR EXCELLENCE</div>
        <div class="feature-main-title">Frontier intelligence tuned for the most demanding loops.</div>
        <div class="feature-grid">
            <div class="feature-card">
                <div class="feature-icon-circle icon-cyan">🎙️</div>
                <div class="feature-num">01 • DUPLEX AUDIO</div>
                <div class="feature-card-title">Duplex Speech Synthesis</div>
                <div class="feature-card-desc">Speak organically with ultra-low latency conversational turns that mirror real executive interview cadences.</div>
            </div>
            <div class="feature-card">
                <div class="feature-icon-circle icon-purple">⚡</div>
                <div class="feature-num">02 • RUBRIC ENGINE</div>
                <div class="feature-card-title">System-Level Evaluation</div>
                <div class="feature-card-desc">Uncompromising scrutiny across architecture trade-offs, operational bottlenecks, and STAR synthesis.</div>
            </div>
            <div class="feature-card">
                <div class="feature-icon-circle icon-blue">📊</div>
                <div class="feature-num">03 • VOCAL RADAR</div>
                <div class="feature-card-title">Real-Time Telemetry & Radar</div>
                <div class="feature-card-desc">Pinpoint filler word densities, speech velocity fluctuations, confidence stability, and semantic conciseness.</div>
            </div>
            <div class="feature-card">
                <div class="feature-icon-circle icon-green">🌐</div>
                <div class="feature-num">04 • DYNAMIC GRAPH</div>
                <div class="feature-card-title">Adaptive Role Intelligence</div>
                <div class="feature-card-desc">Dynamic follow-up questions customized to your actual career resume, target tier-1 benchmarks, and tech stack nuances.</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # BOTTOM CTA BANNER
    st.markdown("""
    <div class="bottom-cta-card">
        <div style="font-size: 0.8rem; font-weight: 700; letter-spacing: 0.1em; color: #818CF8; text-transform: uppercase; margin-bottom: 12px;">
            ACCELERATE YOUR PREPARATION
        </div>
        <div style="font-size: 2.4rem; font-weight: 800; color: #FFFFFF; margin-bottom: 12px; letter-spacing: -0.02em;">
            Your next career milestone begins here.
        </div>
        <div style="font-size: 1.1rem; color: #94A3B8; max-width: 600px; margin: 0 auto 30px auto;">
            Simulate, refine, and walk into your dream loop with absolute confidence.
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_cta_l, col_cta_m, col_cta_r = st.columns([1, 1.4, 1])
    with col_cta_m:
        if st.button("Start Free Practice Session ➜", key="btn_bottom_cta", type="primary", use_container_width=True):
            st.session_state.current_view = "setup" if st.session_state.user else "auth"
            st.rerun()

    # FOOTER
    st.markdown("""
    <div class="app-footer">
        <div>🎯 © 2026 Interview IQ. Designed for candidates targeting the top 1%.</div>
        <div class="footer-links">
            <span>System Architecture</span>
            <span>Security & Privacy</span>
            <span>Terms of Service</span>
            <span style="color: #34D399;">● Systems Nominal</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# VIEW 4: SETUP / PRACTICE CONFIGURATION
# =============================================================================
elif st.session_state.current_view == "setup":

    current_user = st.session_state.user
    if current_user is None:
        st.session_state.current_view = "auth"
        st.rerun()

    stats = db_service.get_user_stats(current_user["id"])

    # User Profile Cockpit Banner
    st.markdown(f"""
    <div class="cockpit-card" style="padding: 24px 30px; margin: 10px auto 25px auto;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 20px;">
            <div style="display: flex; align-items: center; gap: 16px;">
                <div class="interviewer-avatar" style="background: linear-gradient(135deg, #7C3AED 0%, #06B6D4 100%);">
                    👤
                </div>
                <div>
                    <div style="font-size: 1.25rem; font-weight: 800; color: #FFFFFF;">
                        Candidate: <span style="color: #38BDF8;">{current_user['username']}</span>
                    </div>
                    <div style="font-size: 0.85rem; color: #94A3B8;">{current_user['email']}</div>
                </div>
            </div>
            <div style="display: flex; gap: 24px; align-items: center;">
                <div style="text-align: center;">
                    <div style="font-size: 1.8rem; font-weight: 800; color: #818CF8;">{stats['total_quizzes']}</div>
                    <div style="font-size: 0.72rem; text-transform: uppercase; font-weight: 700; color: #94A3B8; letter-spacing: 0.05em;">Quizzes Done</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 1.8rem; font-weight: 800; color: #34D399;">{stats['avg_score']}%</div>
                    <div style="font-size: 0.72rem; text-transform: uppercase; font-weight: 700; color: #94A3B8; letter-spacing: 0.05em;">Avg Score</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 1.8rem; font-weight: 800; color: #FBBF24;">{stats['best_score']}%</div>
                    <div style="font-size: 0.72rem; text-transform: uppercase; font-weight: 700; color: #94A3B8; letter-spacing: 0.05em;">Personal Best</div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Past Quiz History Expander
    if stats["total_quizzes"] > 0:
        with st.expander(f"📜 View Past Quiz History ({stats['total_quizzes']} sessions completed)", expanded=False):
            history_rows = db_service.get_user_history(current_user["id"], limit=10)
            if history_rows:
                for h in history_rows:
                    col_h1, col_h2, col_h3 = st.columns([2.5, 2, 1])
                    with col_h1:
                        st.markdown(f"**{h['role']}** ({h['interview_type']})")
                        st.caption(f"📅 {h['completed_at']}")
                    with col_h2:
                        st.markdown(f"Difficulty: `{h['difficulty']}` | Questions: `{h['total_questions']}`")
                    with col_h3:
                        score_val = h['overall_score']
                        score_color = "#34D399" if score_val >= 80 else ("#FBBF24" if score_val >= 60 else "#F87171")
                        st.markdown(f"<span style='font-size: 1.3rem; font-weight: 800; color: {score_color};'>{score_val:.0f}%</span>", unsafe_allow_html=True)
                    st.divider()

    # Configuration Form
    st.markdown('<div class="cockpit-card" style="margin-top: 15px;">', unsafe_allow_html=True)
    st.markdown("### ⚙️ Configure Your Practice Session")
    st.caption("Customize your target role, difficulty, and upload resume or system design specs for grounded RAG.")

    col_doc, col_cfg = st.columns([1.2, 1], gap="large")

    with col_doc:
        st.markdown("#### 📄 Document Grounding (File Search RAG)")
        st.write(
            "Upload your resume, system architecture document, or job spec. "
            "Our Microsoft Foundry Agent will index it into a Vector Store to tailor authentic questions."
        )

        uploaded_file = st.file_uploader(
            "Upload PDF, DOCX, or TXT (Max 25MB)",
            type=["pdf", "docx", "txt"],
            accept_multiple_files=False,
            help="Files are indexed directly in Microsoft Foundry Vector Store."
        )

        if uploaded_file is not None:
            size_kb = uploaded_file.size / 1024
            st.success(f"✅ Ready to index: **{uploaded_file.name}** ({size_kb:.1f} KB)")
        else:
            st.info("💡 You can also proceed without a document to take a standard profile interview.")

    with col_cfg:
        st.markdown("#### 🎯 Role & Telemetry Parameters")

        role_options = [
            "AI/ML Engineer",
            "Software Engineer",
            "Distributed Systems Architect",
            "Data Scientist",
            "Data Analyst",
            "Python Developer",
            "Custom Role..."
        ]
        selected_role = st.selectbox("Target Role", role_options, index=0)

        custom_role = ""
        if selected_role == "Custom Role...":
            custom_role = st.text_input("Enter your custom role:", placeholder="e.g. Distributed Systems Architect")
            final_role = custom_role.strip() if custom_role.strip() else "Software Engineer"
        else:
            final_role = selected_role

        col_diff, col_type = st.columns(2)
        with col_diff:
            difficulty = st.selectbox("Starting Difficulty", ["Easy", "Medium", "Hard"], index=1)
        with col_type:
            interview_type = st.selectbox("Interview Format", ["Technical", "HR / Behavioral", "Mixed"], index=0)

        total_questions = st.slider(
            "Number of Questions",
            min_value=3,
            max_value=10,
            value=5,
            help="Select question count for your practice loop."
        )

    st.write("")
    start_placeholder = st.empty()
    status_placeholder = st.empty()

    if start_placeholder.button("🚀 Launch Practice Interview Session ➜", type="primary", use_container_width=True):
        start_placeholder.empty()

        vector_store_id = None
        file_id = None
        file_name = None

        with status_placeholder.status("🚀 Launching Interview Cockpit...", expanded=True) as status:
            if uploaded_file is not None:
                status.write("📄 Uploading and indexing document into Microsoft Foundry Vector Store...")
                try:
                    index_result = doc_service.process_and_index_document(uploaded_file)
                    vector_store_id = index_result["vector_store_id"]
                    file_id = index_result["file_id"]
                    file_name = index_result["filename"]
                    status.write(f"✅ Document '{file_name}' indexed successfully in Foundry!")
                except Exception as e:
                    status.update(label="❌ Document Indexing Failed", state="error")
                    st.error(f"Failed to index document in Microsoft Foundry: {str(e)}")
                    st.stop()
            else:
                status.write("ℹ️ No document uploaded — preparing general profile interview.")

            status.write(f"🤖 Generating grounded Question #1 for {final_role} ({difficulty})...")
            try:
                q1 = interview_service.generate_first_question(
                    role=final_role,
                    difficulty=difficulty,
                    interview_type=interview_type,
                    vector_store_id=vector_store_id
                )
                status.write("✅ First question ready!")
            except Exception as e:
                status.update(label="❌ Question Generation Failed", state="error")
                st.error(f"Failed to generate first question from Microsoft Foundry: {str(e)}")
                st.stop()

            status.update(label="🎯 Interview Ready! Launching Cockpit...", state="complete")

        # Update session state and transition to interviewing screen
        st.session_state.role = final_role
        st.session_state.difficulty = difficulty
        st.session_state.current_difficulty = difficulty
        st.session_state.interview_type = interview_type
        st.session_state.total_questions = total_questions
        st.session_state.current_question_index = 1
        st.session_state.current_question = q1
        st.session_state.vector_store_id = vector_store_id
        st.session_state.file_id = file_id
        st.session_state.file_name = file_name
        st.session_state.history = []
        st.session_state.candidate_answer = ""
        st.session_state.last_transcription = ""
        st.session_state.last_evaluation = None
        st.session_state._interview_saved_to_db = False
        st.session_state.stage = "interviewing"
        st.session_state.current_view = "interviewing"

        time.sleep(0.4)
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)


# =============================================================================
# VIEW 5: ACTIVE INTERVIEW COCKPIT (THE CENTERPIECE)
# =============================================================================
elif st.session_state.current_view == "interviewing":

    # Outer Cockpit Container matching reference image
    escaped_q = html.escape(str(st.session_state.current_question).strip())
    q_index_str = f"0{st.session_state.current_question_index}" if st.session_state.current_question_index < 10 else str(st.session_state.current_question_index)
    total_q_str = f"0{st.session_state.total_questions}" if st.session_state.total_questions < 10 else str(st.session_state.total_questions)
    escaped_role = html.escape(str(st.session_state.role))
    escaped_itype = html.escape(str(st.session_state.interview_type))
    escaped_diff = html.escape(str(st.session_state.current_difficulty))

    cockpit_html = (
        f'<div class="cockpit-card" style="margin-top: 5px;">\n'
        f'<div class="cockpit-header">\n'
        f'<div class="interviewer-info">\n'
        f'<div class="interviewer-avatar">🤖</div>\n'
        f'<div>\n'
        f'<div class="interviewer-title">AI Staff Principal Interviewer <span class="master-badge">Master</span></div>\n'
        f'<div class="interviewer-sub">{escaped_role} • {escaped_itype} Depth</div>\n'
        f'</div>\n'
        f'</div>\n'
        f'<div style="display: flex; align-items: center; gap: 16px;">\n'
        f'<span style="font-size: 0.9rem; font-weight: 700; color: #818CF8;">Prompt {q_index_str} / {total_q_str}</span>\n'
        f'<span class="telemetry-chip"><span class="chip-pulse"></span> LIVE DUPLEX 100 FPS</span>\n'
        f'</div>\n'
        f'</div>\n'
        f'<div class="cockpit-prompt-box">\n'
        f'<div class="prompt-tag"><span class="prompt-tag-icon">⚡</span> [{q_index_str}] ACTIVE TECHNICAL PROMPT • {escaped_diff} • {escaped_role}</div>\n'
        f'<p class="prompt-text">"{escaped_q}"</p>\n'
        f'</div>\n'
        f'<div class="mic-center-container">\n'
        f'<div class="glowing-mic-btn">🎙️</div>\n'
        f'<div class="ai-status-pill">● AI Analyzing Concurrency Trade-offs &amp; Structure...</div>\n'
        f'<div class="soundwave-container">\n'
        f'<div class="soundwave-bar"></div>\n'
        f'<div class="soundwave-bar"></div>\n'
        f'<div class="soundwave-bar"></div>\n'
        f'<div class="soundwave-bar"></div>\n'
        f'<div class="soundwave-bar"></div>\n'
        f'<div class="soundwave-bar"></div>\n'
        f'<div class="soundwave-bar"></div>\n'
        f'<div class="soundwave-bar"></div>\n'
        f'</div>\n'
        f'</div>\n'
        f'</div>'
    )
    st.markdown(cockpit_html, unsafe_allow_html=True)

    # Interactive Speech & Audio Input Section
    input_mode = st.radio(
        "Select Answer Mode:",
        ["🎙️ Record Audio (Browser / Microphone)", "💻 Direct PC Microphone (Azure SDK)", "✍️ Type Answer"],
        horizontal=True
    )

    answer_key = f"answer_text_area_{st.session_state.current_question_index}"
    if answer_key not in st.session_state:
        st.session_state[answer_key] = st.session_state.get("candidate_answer", "")

    if input_mode == "🎙️ Record Audio (Browser / Microphone)":
        st.caption("Click the microphone below to record. Azure AI Speech normalizes and transcribes in real-time.")
        audio_prompt = st.audio_input("Record your answer:", key=f"audio_input_q_{st.session_state.current_question_index}")

        if audio_prompt is not None:
            recorded_bytes = audio_prompt.getvalue()
            is_new_audio = recorded_bytes and recorded_bytes != st.session_state.get("_last_seen_audio_bytes")

            col_tr1, col_tr2 = st.columns([1, 2])
            with col_tr1:
                manual_retry = st.button("🔄 Re-transcribe Audio", key=f"btn_retranscribe_{st.session_state.current_question_index}", use_container_width=True)

            if is_new_audio or manual_retry:
                st.session_state._last_seen_audio_bytes = recorded_bytes
                with st.spinner("Transcribing your speech with Azure AI Speech..."):
                    try:
                        transcribed_text = speech_service.transcribe_audio_bytes(
                            recorded_bytes,
                            filename_hint="candidate_speech.wav"
                        )
                        if transcribed_text:
                            st.session_state[answer_key] = transcribed_text
                            st.session_state.candidate_answer = transcribed_text
                            st.session_state["speech_transcribed_success"] = True
                            st.rerun()
                        else:
                            st.warning("⚠️ No clear speech detected. Please speak clearly into your microphone.")
                    except Exception as e:
                        st.error(f"Azure Speech Error: {str(e)}")

    elif input_mode == "💻 Direct PC Microphone (Azure SDK)":
        st.caption("Record directly from host machine default microphone using Azure Speech SDK.")
        col_mic1, col_mic2 = st.columns([1, 2])
        with col_mic1:
            if st.button("🔴 Listen from PC Mic (15s)", type="secondary", use_container_width=True):
                with st.spinner("Listening... Speak your answer now into your PC microphone..."):
                    try:
                        text = speech_service.record_and_transcribe_local_mic(timeout_seconds=15)
                        if text:
                            st.session_state[answer_key] = text
                            st.session_state.candidate_answer = text
                            st.session_state["speech_transcribed_success"] = True
                            st.rerun()
                        else:
                            st.warning("No speech recognized. Please try again.")
                    except Exception as e:
                        st.error(f"PC Mic Error: {str(e)}")

    if st.session_state.pop("speech_transcribed_success", False):
        st.success("✅ Speech successfully transcribed with Azure AI Speech!")

    # Candidate Answer Review & Edit
    st.markdown("#### 📝 Candidate Answer / Transcript (Review & Edit)")
    user_final_answer = st.text_area(
        "You may edit the transcript or type your answer before submitting:",
        key=answer_key,
        height=140,
        placeholder="Your transcribed or typed answer will appear here. Edit as needed..."
    )

    # Real-Time Telemetry Cards
    word_count = len(user_final_answer.split()) if user_final_answer.strip() else 0
    st.markdown(f"""
    <div class="telemetry-grid">
        <div class="telemetry-card">
            <div class="telemetry-card-top">
                <span class="telemetry-card-title">📊 Technical Rigor</span>
                <span class="telemetry-card-score">{"Live Ready" if word_count > 10 else "Awaiting Response"}</span>
            </div>
            <div class="telemetry-metric-sub">
                <span>Role: {st.session_state.role}</span>
                <span>Difficulty: {st.session_state.current_difficulty}</span>
            </div>
        </div>
        <div class="telemetry-card">
            <div class="telemetry-card-top">
                <span class="telemetry-card-title">🗣️ Executive Delivery</span>
                <span class="telemetry-card-score">{word_count} words</span>
            </div>
            <div class="telemetry-metric-sub">
                <span>Format: {st.session_state.interview_type}</span>
                <span>Target: STAR Synthesis</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Submit Action Row
    col_sub1, col_sub2 = st.columns([1, 1])
    with col_sub1:
        st.caption("⏱️ 02:45 / 05:00 • 141ms duplex latency")
    with col_sub2:
        if st.button("Submit Response ✓", type="primary", use_container_width=True):
            if not user_final_answer.strip():
                st.warning("Please speak or type an answer before submitting.")
            else:
                with st.spinner("Submitting to Microsoft Foundry Agent for rubric telemetry..."):
                    try:
                        eval_result = interview_service.evaluate_answer(
                            question=st.session_state.current_question,
                            candidate_answer=user_final_answer.strip(),
                            role=st.session_state.role,
                            difficulty=st.session_state.current_difficulty,
                            vector_store_id=st.session_state.vector_store_id
                        )

                        # Record in history
                        st.session_state.history.append({
                            "question_num": st.session_state.current_question_index,
                            "question": st.session_state.current_question,
                            "answer": user_final_answer.strip(),
                            "difficulty": st.session_state.current_difficulty,
                            "score": eval_result.get("score", 7.0),
                            "what_well": eval_result.get("what_well", []),
                            "what_improve": eval_result.get("what_improve", []),
                            "brief_commentary": eval_result.get("brief_commentary", "")
                        })

                        st.session_state.last_evaluation = eval_result
                        st.session_state.stage = "evaluated"
                        st.session_state.current_view = "evaluated"
                        st.rerun()

                    except Exception as e:
                        st.error(f"Evaluation error: {str(e)}")

    st.markdown('</div>', unsafe_allow_html=True)


# =============================================================================
# VIEW 6: ANSWER EVALUATION TELEMETRY
# =============================================================================
elif st.session_state.current_view == "evaluated":

    eval_data = st.session_state.last_evaluation or {}
    score = eval_data.get("score", 7.0)

    score_color = "#34D399" if score >= 8.0 else ("#FBBF24" if score >= 6.0 else "#F87171")
    score_label = "🌟 Outstanding Performance" if score >= 8.0 else ("💡 Solid Effort — Polish Needed" if score >= 6.0 else "🎯 Foundational Reinforcement Needed")

    good_items_html = "".join([f"<li style='margin-bottom: 8px; color: #E2E8F0;'>{html.escape(str(item))}</li>" for item in eval_data.get("what_well", [])])
    improve_items_html = "".join([f"<li style='margin-bottom: 8px; color: #E2E8F0;'>{html.escape(str(item))}</li>" for item in eval_data.get("what_improve", [])])

    eval_html = (
        f'<div class="cockpit-card">\n'
        f'<div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 20px;">\n'
        f'<div>\n'
        f'<div style="font-size: 0.8rem; font-weight: 700; color: #818CF8; text-transform: uppercase; letter-spacing: 0.08em;">\n'
        f'EVALUATION TELEMETRY • QUESTION 0{st.session_state.current_question_index}\n'
        f'</div>\n'
        f'<div style="font-size: 1.8rem; font-weight: 800; color: #FFFFFF; margin-top: 4px;">\n'
        f'{html.escape(score_label)}\n'
        f'</div>\n'
        f'</div>\n'
        f'<div style="background: rgba(124, 58, 237, 0.15); border: 2px solid {score_color}; border-radius: 16px; padding: 12px 28px; text-align: center;">\n'
        f'<div style="font-size: 2.2rem; font-weight: 800; color: {score_color};">{score:.1f} <span style="font-size: 1.1rem; opacity: 0.7;">/ 10</span></div>\n'
        f'<div style="font-size: 0.75rem; color: #94A3B8; text-transform: uppercase; font-weight: 700;">Rubric Score</div>\n'
        f'</div>\n'
        f'</div>\n'
        f'<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 30px;">\n'
        f'<div class="feedback-col-good" style="background: rgba(16, 185, 129, 0.08); border-left: 5px solid #10B981; padding: 20px; border-radius: 12px;">\n'
        f'<h4 style="color: #34D399; margin-top: 0;">✅ Strengths &amp; Good Points</h4>\n'
        f'<ul style="padding-left: 20px; margin: 0;">{good_items_html}</ul>\n'
        f'</div>\n'
        f'<div class="feedback-col-improve" style="background: rgba(239, 68, 68, 0.08); border-left: 5px solid #EF4444; padding: 20px; border-radius: 12px;">\n'
        f'<h4 style="color: #F87171; margin-top: 0;">💡 Growth Areas &amp; Missing Trade-offs</h4>\n'
        f'<ul style="padding-left: 20px; margin: 0;">{improve_items_html}</ul>\n'
        f'</div>\n'
        f'</div>\n'
        f'</div>'
    )
    st.markdown(eval_html, unsafe_allow_html=True)

    # Next Action Button
    if st.session_state.current_question_index < st.session_state.total_questions:
        next_btn_text = f"➡️ Proceed to Question 0{st.session_state.current_question_index + 1} ➜"
        if st.button(next_btn_text, type="primary", use_container_width=True):
            with st.spinner("Generating adaptive next question based on your performance..."):
                try:
                    next_q_obj = interview_service.generate_next_adaptive_question(
                        role=st.session_state.role,
                        current_difficulty=st.session_state.current_difficulty,
                        interview_type=st.session_state.interview_type,
                        history=st.session_state.history,
                        question_index=st.session_state.current_question_index + 1,
                        total_questions=st.session_state.total_questions,
                        vector_store_id=st.session_state.vector_store_id
                    )

                    st.session_state.current_question_index += 1
                    st.session_state.current_question = next_q_obj["question"]
                    st.session_state.current_difficulty = next_q_obj["new_difficulty"]
                    st.session_state.candidate_answer = ""
                    st.session_state._last_seen_audio_bytes = None
                    st.session_state[f"answer_text_area_{st.session_state.current_question_index}"] = ""
                    st.session_state.stage = "interviewing"
                    st.session_state.current_view = "interviewing"
                    st.rerun()

                except Exception as e:
                    st.error(f"Error generating next question: {str(e)}")

    else:
        st.success("🎉 You have completed all questions in this mock interview loop!")
        if st.button("📊 Synthesize Final Executive Report ➜", type="primary", use_container_width=True):
            with st.spinner("Synthesizing comprehensive rubric report from Microsoft Foundry..."):
                try:
                    report = interview_service.generate_final_report(
                        role=st.session_state.role,
                        difficulty=st.session_state.difficulty,
                        interview_type=st.session_state.interview_type,
                        history=st.session_state.history,
                        vector_store_id=st.session_state.vector_store_id
                    )
                    st.session_state.final_report = report

                    # Persist completed session to SQLite database for this user
                    if st.session_state.user and not st.session_state._interview_saved_to_db:
                        try:
                            overall_score_val = float(report.get("overall_score", 75.0))
                            db_service.save_interview_session(
                                user_id=st.session_state.user["id"],
                                role=st.session_state.role,
                                difficulty=st.session_state.difficulty,
                                interview_type=st.session_state.interview_type,
                                total_questions=st.session_state.total_questions,
                                overall_score=overall_score_val,
                                report_data=report
                            )
                            st.session_state._interview_saved_to_db = True
                        except Exception as dbe:
                            print("DB save session notice:", dbe)

                    st.session_state.stage = "report"
                    st.session_state.current_view = "report"
                    st.rerun()
                except Exception as e:
                    st.error(f"Error generating report: {str(e)}")


# =============================================================================
# VIEW 7: FINAL INTERVIEW REPORT & EXECUTIVE DASHBOARD
# =============================================================================
elif st.session_state.current_view == "report":

    st.balloons()
    report = st.session_state.final_report or {}

    u_name = st.session_state.user['username'] if st.session_state.user else "Candidate"
    st.markdown(f"""
    <div class="cockpit-card">
        <div style="font-size: 0.85rem; font-weight: 700; color: #818CF8; letter-spacing: 0.1em; text-transform: uppercase;">
            EXECUTIVE TELEMETRY REPORT
        </div>
        <div style="font-size: 2.6rem; font-weight: 800; color: #FFFFFF; margin: 6px 0 16px 0;">
            Candidate Performance Synthesis: {u_name}
        </div>
        <div style="font-size: 1rem; color: #94A3B8;">
            Target Role: <b>{st.session_state.role}</b> • Format: <b>{st.session_state.interview_type}</b> • Total Prompts: <b>{st.session_state.total_questions}</b>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Top Metric Score Cards
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)

    with col_m1:
        st.markdown(f"""
        <div class="telemetry-card" style="text-align: center; padding: 24px;">
            <div style="font-size: 2.5rem; font-weight: 800; color: #38BDF8;">{report.get('overall_score', 80)}%</div>
            <div style="font-size: 0.8rem; font-weight: 700; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.08em; margin-top: 6px;">Overall Score</div>
        </div>
        """, unsafe_allow_html=True)

    with col_m2:
        st.markdown(f"""
        <div class="telemetry-card" style="text-align: center; padding: 24px;">
            <div style="font-size: 2.5rem; font-weight: 800; color: #818CF8;">{report.get('technical_knowledge', 80)}%</div>
            <div style="font-size: 0.8rem; font-weight: 700; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.08em; margin-top: 6px;">Technical Depth</div>
        </div>
        """, unsafe_allow_html=True)

    with col_m3:
        st.markdown(f"""
        <div class="telemetry-card" style="text-align: center; padding: 24px;">
            <div style="font-size: 2.5rem; font-weight: 800; color: #34D399;">{report.get('answer_quality', 80)}%</div>
            <div style="font-size: 0.8rem; font-weight: 700; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.08em; margin-top: 6px;">Answer Quality</div>
        </div>
        """, unsafe_allow_html=True)

    with col_m4:
        st.markdown(f"""
        <div class="telemetry-card" style="text-align: center; padding: 24px;">
            <div style="font-size: 2.5rem; font-weight: 800; color: #FBBF24;">{report.get('communication', 80)}%</div>
            <div style="font-size: 0.8rem; font-weight: 700; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.08em; margin-top: 6px;">Communication</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    # Strengths and Improvement Areas
    col_str, col_imp = st.columns(2, gap="large")

    with col_str:
        st.markdown('<div class="feedback-col-good" style="background: rgba(16, 185, 129, 0.08); border-left: 5px solid #10B981; padding: 20px; border-radius: 12px;">', unsafe_allow_html=True)
        st.markdown("### 🌟 Validated Strengths")
        for s in report.get("strengths", []):
            st.markdown(f"- {s}")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_imp:
        st.markdown('<div class="feedback-col-improve" style="background: rgba(239, 68, 68, 0.08); border-left: 5px solid #EF4444; padding: 20px; border-radius: 12px;">', unsafe_allow_html=True)
        st.markdown("### 🎯 Critical Areas for Improvement")
        for imp in report.get("areas_for_improvement", []):
            st.markdown(f"- {imp}")
        st.markdown('</div>', unsafe_allow_html=True)

    # Question-by-Question Breakdown
    st.write("")
    st.markdown("### 📝 Question-wise Telemetry Breakdown")
    for item in st.session_state.history:
        q_num = item.get("question_num", 1)
        q_score = item.get("score", 7.0)
        with st.expander(f"Question 0{q_num}: {item.get('question')} (Score: {q_score:.1f}/10)", expanded=True):
            st.markdown(f"**Your Answer:**\n> {item.get('answer')}")
            col_q1, col_q2 = st.columns(2)
            with col_q1:
                st.markdown("**What you did well:**")
                for w in item.get("what_well", []):
                    st.markdown(f"- {w}")
            with col_q2:
                st.markdown("**Growth opportunities:**")
                for i in item.get("what_improve", []):
                    st.markdown(f"- {i}")

    # Recommended Preparation Topics
    st.write("")
    st.markdown("### 📚 Recommended Preparation & Next Steps")
    prep_topics = report.get("recommended_preparation", [])
    if prep_topics:
        for t in prep_topics:
            st.markdown(f"- 📌 **{t}**")
    else:
        st.markdown("- Review architectural trade-offs and operational bottlenecks.")
        st.markdown("- Practice concise STAR delivery for technical narratives.")

    st.divider()

    st.write("")
    if st.button("🔄 Launch Another Practice Loop ➜", type="primary", use_container_width=True):
        reset_interview()
        st.session_state.current_view = "setup"
        st.rerun()
