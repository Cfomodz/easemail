#!/usr/bin/env python3
"""
Opt-out Manager for Email Triage System
Handles data erasure requests and repeat offender tracking
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import re

class OptOutManager:
    """Manages opt-out requests and repeat offender tracking"""
    
    def __init__(self, data_dir: str = "./triage_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.opt_out_file = self.data_dir / "opt_out_requests.json"
        self.opt_out_data = self._load_opt_out_data()
    
    def _load_opt_out_data(self) -> Dict:
        """Load opt-out request data"""
        if self.opt_out_file.exists():
            with open(self.opt_out_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_opt_out_data(self):
        """Save opt-out request data"""
        with open(self.opt_out_file, 'w') as f:
            json.dump(self.opt_out_data, f, indent=2, default=str)
    
    def _extract_domain(self, email_address: str) -> str:
        """Extract domain from email address"""
        if '@' in email_address:
            return email_address.split('@')[-1].lower()
        return email_address.lower()
    
    def record_opt_out_request(self, sender_email: str) -> Dict:
        """Record an opt-out request and return request info"""
        domain = self._extract_domain(sender_email)
        current_time = datetime.now()
        
        if domain not in self.opt_out_data:
            self.opt_out_data[domain] = {
                'sender_email': sender_email,
                'requests': [],
                'is_repeat_offender': False
            }
        
        # Add new request to the list
        self.opt_out_data[domain]['requests'].append({
            'date': current_time.isoformat(),
            'sender_email': sender_email
        })
        
        # Check if this makes them a repeat offender
        requests = self.opt_out_data[domain]['requests']
        if len(requests) >= 2:
            # Check if latest request is more than 7 days after first
            first_request = datetime.fromisoformat(requests[0]['date'])
            latest_request = current_time
            
            if (latest_request - first_request).days >= 7:
                self.opt_out_data[domain]['is_repeat_offender'] = True
        
        self._save_opt_out_data()
        
        return {
            'domain': domain,
            'request_count': len(requests),
            'is_repeat_offender': self.opt_out_data[domain]['is_repeat_offender'],
            'first_request_date': requests[0]['date'] if requests else None
        }
    
    def is_repeat_offender(self, sender_email: str) -> bool:
        """Check if sender is a repeat offender"""
        domain = self._extract_domain(sender_email)
        return self.opt_out_data.get(domain, {}).get('is_repeat_offender', False)
    
    def get_opt_out_stats(self) -> Dict:
        """Get opt-out statistics"""
        total_domains = len(self.opt_out_data)
        repeat_offenders = sum(1 for data in self.opt_out_data.values() if data.get('is_repeat_offender', False))
        total_requests = sum(len(data.get('requests', [])) for data in self.opt_out_data.values())
        
        return {
            'total_domains': total_domains,
            'repeat_offenders': repeat_offenders,
            'total_requests': total_requests
        }
    
    def generate_data_erasure_draft(self, sender_email: str, subject: str) -> Dict:
        """Generate a data erasure request draft email"""
        
        # Standard data erasure request text
        body = """To Whom It May Concern:

I am hereby requesting immediate erasure of personal data concerning me. If I have given consent to the processing of my personal data, I am hereby withdrawing said consent. 

If you have made the aforementioned data public, please take all reasonable steps for the erasure of all links, copies or replications. This applies not only to exact copies of the data concerned, but also to those from which information contained in the data concerned can be derived.

I am including the following information necessary to identify me: email address/username/login associated with this email.

Thank you in advance.

"""
        
        # Generate subject
        reply_subject = f"Re: {subject}" if not subject.startswith("Re:") else subject
        if "data erasure" not in reply_subject.lower():
            reply_subject += " - Data Erasure Request"
        
        return {
            'to': sender_email,
            'subject': reply_subject,
            'body': body,
            'timestamp': datetime.now().isoformat()
        }


def main():
    """Test the opt-out manager"""
    manager = OptOutManager()
    
    # Test recording opt-out requests
    test_emails = [
        "marketing@spammer.com",
        "newsletter@badcompany.com", 
        "marketing@spammer.com"  # Repeat from same domain
    ]
    
    print("🚫 Testing Opt-Out Manager")
    print("="*40)
    
    for email in test_emails:
        print(f"\n📧 Processing opt-out for: {email}")
        result = manager.record_opt_out_request(email)
        print(f"   Domain: {result['domain']}")
        print(f"   Request count: {result['request_count']}")
        print(f"   Repeat offender: {result['is_repeat_offender']}")
        
        # Generate draft
        draft = manager.generate_data_erasure_draft(email, "Weekly Newsletter")
        print(f"   Draft subject: {draft['subject']}")
    
    # Show stats
    stats = manager.get_opt_out_stats()
    print(f"\n📊 Opt-out Statistics:")
    print(f"   Total domains: {stats['total_domains']}")
    print(f"   Repeat offenders: {stats['repeat_offenders']}")
    print(f"   Total requests: {stats['total_requests']}")


if __name__ == "__main__":
    main()
