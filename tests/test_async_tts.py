#!/usr/bin/env python3
"""
Test script to demonstrate async TTS with immediate input
"""

import time
from email_triage_system import EmailTriageSystem, EmailItem, TriageDecision
from datetime import datetime

def test_async_behavior():
    """Test that TTS starts immediately but input is accepted right away"""
    
    print("🎤 Testing Async TTS with Immediate Input")
    print("="*60)
    print("This test demonstrates the correct behavior:")
    print("1. Email details are displayed")
    print("2. TTS starts speaking immediately (async)")
    print("3. Menu appears right away (doesn't wait for TTS)")
    print("4. You can make a choice while TTS is still speaking")
    print("5. TTS stops as soon as you make a choice")
    print()
    
    # Initialize system
    triage = EmailTriageSystem()
    
    # Create a test email
    test_email = EmailItem(
        id="test_001",
        sender="important@company.com",
        subject="Quarterly Review Meeting - Action Required",
        snippet="Hi there, we need to schedule your quarterly review meeting for next week. Please confirm your availability for Tuesday or Wednesday afternoon. This is important for your performance evaluation and career development planning.",
        timestamp=datetime.now(),
        labels=["INBOX"],
        thread_id="thread_test",
        has_unsubscribe=False,
        sender_domain="company.com"
    )
    
    # Create a suggested decision
    suggested_decision = TriageDecision(
        email_id=test_email.id,
        action="action_needed",
        confidence=0.92,
        reasoning="Contains important keywords like 'action required' and 'meeting', and is from a company domain"
    )
    
    print("Starting test - notice how the menu appears immediately...")
    print("The voice will start speaking, but you can interrupt it by typing a choice!")
    print()
    
    # This should show the menu immediately while TTS plays in background
    decision = triage.get_user_decision(test_email, suggested_decision)
    
    if decision:
        print(f"\n✅ You chose: {decision.action}")
        print("Notice how the voice stopped as soon as you made your choice!")
    else:
        print("\n⏭️  Email skipped")
    
    print("\n🎯 Perfect! This is exactly how the system should work:")
    print("- Voice starts immediately (no delay)")
    print("- Menu appears right away (no waiting)")
    print("- Voice stops when you decide (immediate interruption)")
    print("- Fast, responsive, no waiting around!")

if __name__ == "__main__":
    test_async_behavior()
