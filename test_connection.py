"""
test_connection.py
Comprehensive diagnostic test script for Interview IQ:
1. Validates Microsoft Foundry Project connection & DefaultAzureCredential
2. Verifies AI-Interview-Coach Agent configuration and GPT-4.1-mini deployment
3. Verifies Azure AI Speech STT service and credentials
"""

import sys
import os
from dotenv import load_dotenv

load_dotenv()

# Ensure UTF-8 console output on Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

print("=" * 60)
print("  Interview IQ - Diagnostic & Health Check")
print("=" * 60)

# 1. Test Azure Identity & Microsoft Foundry
print("\n[1/3] Testing Microsoft Foundry Project Connection...")
try:
    from services.foundry_service import get_foundry_service
    foundry = get_foundry_service()
    status = foundry.verify_connection()
    if status.get("success"):
        print("  [OK] Successfully connected to Microsoft Foundry!")
        print(f"  Project Endpoint: {status.get('endpoint')}")
        print(f"  Active Agents: {status.get('agents')}")
    else:
        print(f"  [FAIL] Foundry connection failed: {status.get('error')}")
except Exception as e:
    print(f"  [ERROR] Could not initialize Foundry: {e}")

# 2. Test Agent Details & GPT-4.1-mini
print("\n[2/3] Checking Foundry Agent 'AI-Interview-Coach'...")
try:
    agent_info = foundry.get_agent_details()
    print(f"  [OK] Agent Name: {agent_info.get('name')}")
    print(f"  Model: {agent_info.get('model')}")
    print(f"  Instructions configured: {'Yes' if agent_info.get('instructions') else 'No'}")
except Exception as e:
    print(f"  [ERROR] Agent check failed: {e}")

# 3. Test Azure AI Speech Service
print("\n[3/3] Checking Azure AI Speech Service...")
try:
    from services.speech_service import get_speech_service
    speech = get_speech_service()
    speech_stat = speech.verify_speech_service()
    if speech_stat.get("success"):
        print(f"  [OK] Azure Speech initialized for region: {speech_stat.get('region')}")
    else:
        print(f"  [FAIL] Azure Speech check failed: {speech_stat.get('error')}")
except Exception as e:
    print(f"  [ERROR] Speech service check error: {e}")

print("\n" + "=" * 60)
print("Diagnostic test completed.")
print("=" * 60)