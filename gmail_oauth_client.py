#!/usr/bin/env python3
"""
Direct Gmail OAuth Client for Email Triage System
Simple, direct integration with Gmail API using OAuth
"""

import json
import os
import pickle
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

# Gmail API imports
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    HAS_GMAIL_API = True
except ImportError:
    HAS_GMAIL_API = False

from email_triage_system import EmailItem, EmailTriageSystem, TriageDecision

# Gmail API scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.labels'
]

class GmailOAuthClient:
    """Direct Gmail OAuth client"""
    
    def __init__(self, credentials_file: str = "credentials.json", token_file: str = "token.pickle"):
        if not HAS_GMAIL_API:
            print("❌ Gmail API libraries not installed")
            print("Install with: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
            exit(1)
        
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Gmail using OAuth"""
        creds = None
        
        # Load existing token
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("🔄 Refreshing Gmail credentials...")
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    print(f"❌ Gmail credentials file not found: {self.credentials_file}")
                    print("📋 To set up Gmail OAuth:")
                    print("1. Go to https://console.cloud.google.com/")
                    print("2. Create a new project or select existing")
                    print("3. Enable Gmail API")
                    print("4. Create OAuth 2.0 credentials (Desktop application)")
                    print("5. Download credentials.json to this directory")
                    exit(1)
                
                print("🔐 Starting Gmail OAuth flow...")
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        # Build Gmail service
        self.service = build('gmail', 'v1', credentials=creds)
        print("✅ Gmail OAuth authentication successful")
    
    def list_messages(self, query: str = "in:inbox", max_results: int = 100) -> List[Dict]:
        """List messages from Gmail"""
        try:
            result = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = result.get('messages', [])
            print(f"📧 Found {len(messages)} messages")
            return messages
            
        except Exception as e:
            print(f"❌ Error listing messages: {e}")
            return []
    
    def get_message(self, message_id: str) -> Dict:
        """Get full message details"""
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            return message
            
        except Exception as e:
            print(f"❌ Error getting message {message_id}: {e}")
            return {}
    
    def modify_message(self, message_id: str, add_labels: List[str] = None, remove_labels: List[str] = None):
        """Modify message labels"""
        try:
            body = {
                'addLabelIds': add_labels or [],
                'removeLabelIds': remove_labels or []
            }
            
            result = self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body=body
            ).execute()
            
            return result
            
        except Exception as e:
            print(f"❌ Error modifying message {message_id}: {e}")
            return {}
    
    def trash_message(self, message_id: str):
        """Move message to trash"""
        try:
            result = self.service.users().messages().trash(
                userId='me',
                id=message_id
            ).execute()
            
            print(f"🗑️ Trashed message {message_id}")
            return result
            
        except Exception as e:
            print(f"❌ Error trashing message {message_id}: {e}")
            return {}
    
    def archive_message(self, message_id: str):
        """Archive message (remove from inbox)"""
        return self.modify_message(message_id, remove_labels=['INBOX'])
    
    def search_messages_by_sender_subject(self, sender: str, subject: str, exclude_conversations: bool = True) -> List[Dict]:
        """Search for messages by sender and subject, excluding conversations"""
        try:
            # Clean the subject for searching (remove Re:, Fwd:, etc.)
            clean_subject = subject
            for prefix in ['Re:', 'RE:', 'Fwd:', 'FWD:', 'Fw:', 'FW:']:
                if clean_subject.startswith(prefix):
                    clean_subject = clean_subject[len(prefix):].strip()
            
            # Build search query
            query = f'from:"{sender}" subject:"{clean_subject}"'
            
            # Get all matching messages
            result = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=500  # Reasonable limit
            ).execute()
            
            messages = result.get('messages', [])
            
            if exclude_conversations:
                # Filter out messages that are part of conversations (threads with >1 message)
                single_messages = []
                for msg in messages:
                    # Get thread info to check message count
                    thread_id = msg.get('threadId')
                    if thread_id:
                        thread_result = self.service.users().threads().get(
                            userId='me',
                            id=thread_id
                        ).execute()
                        
                        # Only include if thread has exactly 1 message (no conversation)
                        if len(thread_result.get('messages', [])) == 1:
                            single_messages.append(msg)
                
                return single_messages
            
            return messages
            
        except Exception as e:
            print(f"❌ Error searching messages: {e}")
            return []
    
    def mark_as_read(self, message_id: str):
        """Mark message as read"""
        try:
            result = self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            return result
        except Exception as e:
            print(f"❌ Error marking as read {message_id}: {e}")
            return {}
    
    def create_labels_if_needed(self):
        """Create triage labels if they don't exist"""
        try:
            # Get existing labels
            labels_result = self.service.users().labels().list(userId='me').execute()
            existing_labels = {label['name']: label['id'] for label in labels_result.get('labels', [])}
            
            # Labels we need
            needed_labels = ['TRIAGE_REVISIT', 'TRIAGE_ACTION_NEEDED', 'TRIAGE_OPT_OUT']
            
            for label_name in needed_labels:
                if label_name not in existing_labels:
                    print(f"📝 Creating label: {label_name}")
                    label_body = {
                        'name': label_name,
                        'labelListVisibility': 'labelShow',
                        'messageListVisibility': 'show'
                    }
                    
                    self.service.users().labels().create(
                        userId='me',
                        body=label_body
                    ).execute()
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating labels: {e}")
            return False


class SimpleGmailTriageConnector:
    """Simple Gmail triage connector using direct OAuth"""
    
    def __init__(self, credentials_file: str = "credentials.json"):
        print("🔗 Connecting to Gmail via OAuth...")
        self.gmail_client = GmailOAuthClient(credentials_file)
        self.triage_system = EmailTriageSystem()
        
        # Create labels if needed
        self.gmail_client.create_labels_if_needed()
        
        # Label mappings
        self.labels = {
            'trash': 'TRASH',
            'revisit': 'TRIAGE_REVISIT',
            'action_needed': 'TRIAGE_ACTION_NEEDED',
            'spam': 'SPAM',
            'opt_out': 'TRIAGE_OPT_OUT'
        }
    
    def gmail_to_email_item(self, message_data: Dict) -> EmailItem:
        """Convert Gmail message to EmailItem"""
        headers = message_data.get('payload', {}).get('headers', [])
        
        # Extract header values
        sender = ""
        subject = ""
        date_str = ""
        
        for header in headers:
            name = header.get('name', '').lower()
            value = header.get('value', '')
            
            if name == 'from':
                sender = value
            elif name == 'subject':
                subject = value
            elif name == 'date':
                date_str = value
        
        # Get snippet
        snippet = message_data.get('snippet', '')
        
        # Check for unsubscribe links
        has_unsubscribe = False
        unsubscribe_link = ""
        
        for header in headers:
            if header.get('name', '').lower() == 'list-unsubscribe':
                has_unsubscribe = True
                # Extract URL from header
                import re
                url_match = re.search(r'<(https?://[^>]+)>', header.get('value', ''))
                if url_match:
                    unsubscribe_link = url_match.group(1)
                break
        
        return EmailItem(
            id=message_data.get('id', ''),
            sender=sender,
            subject=subject,
            snippet=snippet,
            timestamp=datetime.now(),  # Could parse date_str for accuracy
            labels=message_data.get('labelIds', []),
            thread_id=message_data.get('threadId', ''),
            has_unsubscribe=has_unsubscribe,
            unsubscribe_link=unsubscribe_link
        )
    
    def fetch_inbox_emails(self, max_count: int = 50) -> List[EmailItem]:
        """Fetch emails from inbox, excluding already triaged ones"""
        print(f"📥 Fetching up to {max_count} emails from inbox...")
        
        # Query to exclude already processed emails
        query = "in:inbox -label:TRIAGE_REVISIT -label:TRIAGE_ACTION_NEEDED -label:TRIAGE_OPT_OUT"
        
        # Get message list
        messages = self.gmail_client.list_messages(query=query, max_results=max_count)
        
        # Get full message details
        email_items = []
        for i, msg in enumerate(messages):
            print(f"📧 Processing email {i+1}/{len(messages)}...", end='\r')
            
            full_msg = self.gmail_client.get_message(msg['id'])
            if full_msg:
                email_item = self.gmail_to_email_item(full_msg)
                email_items.append(email_item)
        
        print(f"\n✅ Fetched {len(email_items)} emails")
        return email_items
    
    def apply_triage_decisions(self, decisions: List[tuple]):
        """Apply triage decisions to Gmail"""
        print(f"\n📋 Applying {len(decisions)} triage decisions...")
        
        for email_item, decision in decisions:
            try:
                if decision.action == 'trash':
                    self.gmail_client.trash_message(email_item.id)
                    
                elif decision.action == 'revisit':
                    # Remove from inbox, add revisit label
                    self.gmail_client.modify_message(
                        email_item.id,
                        add_labels=[self.labels['revisit']],
                        remove_labels=['INBOX']
                    )
                    print(f"📦 Moved to revisit: {email_item.subject[:50]}...")
                
                elif decision.action == 'action_needed':
                    # Keep in inbox, add action needed label
                    self.gmail_client.modify_message(
                        email_item.id,
                        add_labels=[self.labels['action_needed']]
                    )
                    print(f"⚡ Marked action needed: {email_item.subject[:50]}...")
                
                elif decision.action == 'opt_out':
                    # Handle opt-out: create draft and archive
                    self._handle_opt_out_action(email_item, decision)
                    
                elif decision.action == 'spam':
                    # Mark as spam for repeat offenders
                    self._handle_spam_action(email_item, decision)
                
                elif decision.action == 'bulk_archive':
                    # Handle bulk archive for sender/subject
                    self._handle_bulk_archive_action(email_item, decision)
                
            except Exception as e:
                print(f"❌ Failed to apply {decision.action} to {email_item.id}: {e}")
    
    def _handle_opt_out_action(self, email_item: EmailItem, decision: TriageDecision):
        """Handle opt-out action: create draft and archive"""
        try:
            # Extract draft info from decision
            if decision.suggested_rule and "opt_out_data:" in decision.suggested_rule:
                draft_data_str = decision.suggested_rule.split("opt_out_data:", 1)[1]
                # Parse the draft info (simplified parsing)
                print(f"🚫 Creating data erasure draft for: {email_item.sender}")
                
                # For now, just archive and add opt-out label
                # TODO: Implement actual draft creation via Gmail API
                self.gmail_client.modify_message(
                    email_item.id,
                    add_labels=[self.labels['opt_out']],
                    remove_labels=['INBOX']
                )
                print(f"📧 Opt-out processed: {email_item.subject[:50]}...")
                print(f"💡 Draft creation would be implemented here")
            
        except Exception as e:
            print(f"❌ Error handling opt-out: {e}")
    
    def _handle_spam_action(self, email_item: EmailItem, decision: TriageDecision):
        """Handle spam action for repeat offenders"""
        try:
            # Mark as spam and remove from inbox
            self.gmail_client.modify_message(
                email_item.id,
                add_labels=['SPAM'],
                remove_labels=['INBOX']
            )
            print(f"🚫 Marked as SPAM (repeat offender): {email_item.subject[:50]}...")
            
        except Exception as e:
            print(f"❌ Error marking as spam: {e}")
    
    def _handle_bulk_archive_action(self, email_item: EmailItem, decision: TriageDecision):
        """Handle bulk archive action for sender/subject"""
        try:
            # Extract bulk info from decision
            if decision.suggested_rule and "bulk_archive_data:" in decision.suggested_rule:
                bulk_data_str = decision.suggested_rule.split("bulk_archive_data:", 1)[1]
                # Parse the bulk info (simplified parsing)
                print(f"📚 Searching for emails from {email_item.sender} with subject '{email_item.subject}'...")
                
                # Search for matching emails (single threads only)
                matching_messages = self.gmail_client.search_messages_by_sender_subject(
                    email_item.sender, 
                    email_item.subject,
                    exclude_conversations=True
                )
                
                if matching_messages:
                    print(f"📧 Found {len(matching_messages)} matching emails (single threads only)")
                    
                    # Process each matching email
                    archived_count = 0
                    for msg in matching_messages:
                        try:
                            msg_id = msg['id']
                            # Mark as read and archive
                            self.gmail_client.mark_as_read(msg_id)
                            self.gmail_client.archive_message(msg_id)
                            archived_count += 1
                        except Exception as e:
                            print(f"⚠️  Failed to process message {msg_id}: {e}")
                    
                    print(f"✅ Bulk archived {archived_count} emails from {email_item.sender}")
                else:
                    print(f"📭 No matching single-thread emails found")
            
        except Exception as e:
            print(f"❌ Error handling bulk archive: {e}")
    
    def run_triage_session(self, batch_size: int = 5):
        """Run a complete triage session"""
        print("🚀 Starting Gmail Triage Session")
        print("="*60)
        
        # Fetch emails
        emails = self.fetch_inbox_emails(batch_size)
        
        if not emails:
            print("📭 No emails to process!")
            return
        
        # Process with triage system
        decisions = self.triage_system.process_batch(emails)
        
        # Apply decisions to Gmail
        if decisions:
            self.apply_triage_decisions(decisions)
        
        # Print final stats
        self.triage_system.print_session_stats()


def main():
    """Main function"""
    print("📧 Simple Gmail Triage System")
    print("Direct OAuth integration - simple and reliable!")
    print()
    
    try:
        # Initialize connector
        connector = SimpleGmailTriageConnector()
        
        # Run triage session
        connector.run_triage_session(batch_size=5)
        
    except KeyboardInterrupt:
        print("\n👋 Triage session interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during triage session: {e}")


if __name__ == "__main__":
    main()
