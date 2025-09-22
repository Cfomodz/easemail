#!/usr/bin/env python3
"""
AI Email Triage System
A smart email processing system that learns your preferences and provides
simple yes/no decisions for batch email management.

Features:
- AI-powered email classification
- Three-pile sorting system (Trash, Revisit, Action Needed)
- Preference learning and rule generation
- Automated unsubscribe/data erasure requests
- Single-click batch approvals
- Text-to-speech for hands-free operation
"""

import json
import os
import re
import sqlite3
import sys
import termios
import tty
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib

# Optional imports - will gracefully degrade if not available
try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# Import our TTS manager
try:
    from tts_manager import TTSManager
    HAS_TTS_MANAGER = True
except ImportError:
    HAS_TTS_MANAGER = False
    try:
        import pyttsx3
        HAS_TTS = True
    except ImportError:
        HAS_TTS = False

# Import opt-out manager
try:
    from opt_out_manager import OptOutManager
    HAS_OPT_OUT = True
except ImportError:
    HAS_OPT_OUT = False


@dataclass
class EmailItem:
    """Represents an email item for processing"""
    id: str
    sender: str
    subject: str
    snippet: str
    timestamp: datetime
    labels: List[str]
    thread_id: str
    has_unsubscribe: bool = False
    unsubscribe_link: str = ""
    sender_domain: str = ""
    
    def __post_init__(self):
        if not self.sender_domain and '@' in self.sender:
            self.sender_domain = self.sender.split('@')[-1]


@dataclass
class TriageDecision:
    """Represents a triage decision"""
    email_id: str
    action: str  # 'trash', 'revisit', 'action_needed'
    confidence: float
    reasoning: str
    suggested_rule: Optional[str] = None


@dataclass
class UserPreference:
    """Represents a learned user preference"""
    pattern_type: str  # 'sender', 'domain', 'subject_keyword', 'content_pattern'
    pattern_value: str
    action: str
    confidence: float
    created_at: datetime
    usage_count: int = 0


def getch():
    """Get a single character from stdin without pressing enter"""
    try:
        # Unix/Linux/macOS
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch
    except:
        # Fallback for Windows or if termios fails
        try:
            import msvcrt
            return msvcrt.getch().decode('utf-8')
        except:
            # Final fallback - use regular input
            return input("Press key: ").strip().lower()


class EmailTriageSystem:
    """Main email triage system"""
    
    def __init__(self, data_dir: str = "./triage_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Initialize database
        self.db_path = self.data_dir / "preferences.db"
        self.init_database()
        
        # Load configuration first
        self.config = self.load_config()
        
        # Initialize opt-out manager
        self.opt_out_manager = None
        if HAS_OPT_OUT:
            try:
                self.opt_out_manager = OptOutManager(str(self.data_dir))
            except Exception as e:
                print(f"⚠️  Opt-out manager initialization failed: {e}")
        
        # Initialize TTS after config is loaded
        self.tts_manager = None
        if HAS_TTS_MANAGER:
            try:
                self.tts_manager = TTSManager(self.config)
            except Exception as e:
                print(f"⚠️  TTS Manager initialization failed: {e}")
        elif HAS_TTS:
            try:
                import pyttsx3
                self.tts_engine = pyttsx3.init()
                self.tts_engine.setProperty('rate', 180)  # Slightly faster speech
            except:
                pass
        
        # Statistics
        self.session_stats = {
            'processed': 0,
            'trash': 0,
            'revisit': 0,
            'action_needed': 0,
            'auto_decided': 0
        }
    
    def init_database(self):
        """Initialize SQLite database for preferences"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT NOT NULL,
                pattern_value TEXT NOT NULL,
                action TEXT NOT NULL,
                confidence REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                usage_count INTEGER DEFAULT 0,
                UNIQUE(pattern_type, pattern_value, action)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email_id TEXT NOT NULL,
                sender TEXT,
                subject TEXT,
                action TEXT NOT NULL,
                reasoning TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                was_auto_decided BOOLEAN DEFAULT FALSE
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def load_config(self) -> Dict:
        """Load configuration from file"""
        config_path = self.data_dir / "config.json"
        default_config = {
            "openai_api_key": "",
            "auto_decide_threshold": 0.85,
            "enable_tts": True,
            "enable_auto_unsubscribe": True,
            "unsubscribe_domains_whitelist": [
                "github.com", "stackoverflow.com", "medium.com"
            ],
            "marketing_keywords": [
                "unsubscribe", "marketing", "newsletter", "promotion", 
                "sale", "offer", "deal", "discount", "limited time"
            ],
            "important_keywords": [
                "urgent", "important", "action required", "deadline",
                "invoice", "payment", "security", "verification"
            ]
        }
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
                # Merge with defaults
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
        else:
            config = default_config
            self.save_config(config)
        
        return config
    
    def save_config(self, config: Dict):
        """Save configuration to file"""
        config_path = self.data_dir / "config.json"
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
    
    def speak(self, text: str):
        """Text-to-speech output (blocking)"""
        if self.tts_manager and self.config.get('enable_tts', True):
            # Use the advanced TTS manager
            self.tts_manager.speak(text)
        elif hasattr(self, 'tts_engine') and self.tts_engine and self.config.get('enable_tts', True):
            # Fallback to basic pyttsx3
            try:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            except:
                pass
        else:
            # Text fallback
            print(f"🔊 {text}")
    
    def speak_async(self, text: str):
        """Text-to-speech output (non-blocking)"""
        if self.tts_manager and self.config.get('enable_tts', True):
            # Use the advanced TTS manager's async method
            self.tts_manager.speak_async(text)
        elif hasattr(self, 'tts_engine') and self.tts_engine and self.config.get('enable_tts', True):
            # Fallback to basic pyttsx3 in a thread
            import threading
            def speak_thread():
                try:
                    self.tts_engine.say(text)
                    self.tts_engine.runAndWait()
                except:
                    pass
            thread = threading.Thread(target=speak_thread, daemon=True)
            thread.start()
        else:
            # Text fallback
            print(f"🔊 {text}")
    
    def _speak_email_details_staged(self, email: EmailItem, suggested_decision: TriageDecision):
        """Speak email details in stages: AI suggestion first, then details"""
        import threading
        import time
        
        def staged_speech():
            try:
                # Stage 1: AI suggestion (most important - speak immediately)
                stage1_text = f"Should I {suggested_decision.action}"
                if self.tts_manager:
                    self.tts_manager.speak(stage1_text, interruptible=True)
                else:
                    print(f"🔊 {stage1_text}")
                
                # Brief pause to allow user to process and potentially interrupt
                time.sleep(0.5)
                
                # Check if we should continue (not interrupted)
                if self.tts_manager and hasattr(self.tts_manager, 'interrupt_flag'):
                    if self.tts_manager.interrupt_flag.is_set():
                        return
                
                # Stage 2: Email details
                stage2_text = f"Email from {email.sender}. Subject: {email.subject}."
                if self.tts_manager:
                    self.tts_manager.speak(stage2_text, interruptible=True)
                else:
                    print(f"🔊 {stage2_text}")
                
                # Another brief pause
                time.sleep(0.3)
                
                # Check again for interruption
                if self.tts_manager and hasattr(self.tts_manager, 'interrupt_flag'):
                    if self.tts_manager.interrupt_flag.is_set():
                        return
                
                # Stage 3: Reasoning (least critical)
                if len(suggested_decision.reasoning) < 100:  # Only if reasoning is short
                    stage3_text = suggested_decision.reasoning
                    if self.tts_manager:
                        self.tts_manager.speak(stage3_text, interruptible=True)
                    else:
                        print(f"🔊 {stage3_text}")
                        
            except Exception as e:
                print(f"⚠️  Staged speech error: {e}")
        
        # Start staged speech in background thread
        speech_thread = threading.Thread(target=staged_speech, daemon=True)
        speech_thread.start()
    
    def classify_email_ai(self, email: EmailItem) -> TriageDecision:
        """Use AI to classify email"""
        if not HAS_OPENAI or not self.config.get('openai_api_key'):
            return self.classify_email_rules(email)
        
        try:
            client = openai.OpenAI(api_key=self.config['openai_api_key'])
            
            # Get existing preferences for context
            preferences = self.get_learned_preferences()
            pref_context = "\n".join([
                f"- {p.pattern_type}:{p.pattern_value} → {p.action} (confidence: {p.confidence:.2f})"
                for p in preferences[:10]  # Top 10 most confident
            ])
            
            prompt = f"""
You are an email triage assistant. Classify this email into one of three categories:
1. "trash" - Marketing, spam, newsletters, notifications that can be safely ignored/archived
2. "revisit" - Might be important but not urgent, review later when inbox is clean
3. "action_needed" - Requires immediate human attention, response, or action

Email Details:
- Sender: {email.sender}
- Subject: {email.subject}
- Snippet: {email.snippet}
- Has unsubscribe link: {email.has_unsubscribe}

Learned Preferences (for context):
{pref_context}

Respond with JSON:
{{
    "action": "trash|revisit|action_needed",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation",
    "suggested_rule": "optional rule for future similar emails"
}}
"""
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            result = json.loads(response.choices[0].message.content)
            return TriageDecision(
                email_id=email.id,
                action=result['action'],
                confidence=result['confidence'],
                reasoning=result['reasoning'],
                suggested_rule=result.get('suggested_rule')
            )
            
        except Exception as e:
            print(f"AI classification failed: {e}")
            return self.classify_email_rules(email)
    
    def classify_email_rules(self, email: EmailItem) -> TriageDecision:
        """Classify email using learned rules and heuristics"""
        # Check learned preferences first
        preferences = self.get_matching_preferences(email)
        if preferences:
            best_pref = max(preferences, key=lambda p: p.confidence)
            if best_pref.confidence > 0.7:
                return TriageDecision(
                    email_id=email.id,
                    action=best_pref.action,
                    confidence=best_pref.confidence,
                    reasoning=f"Learned preference: {best_pref.pattern_type}={best_pref.pattern_value}"
                )
        
        # Heuristic classification
        subject_lower = email.subject.lower()
        snippet_lower = email.snippet.lower()
        combined_text = f"{subject_lower} {snippet_lower}"
        
        # High priority indicators
        important_keywords = self.config.get('important_keywords', [])
        if any(keyword in combined_text for keyword in important_keywords):
            return TriageDecision(
                email_id=email.id,
                action="action_needed",
                confidence=0.8,
                reasoning="Contains important keywords"
            )
        
        # Marketing/newsletter indicators
        marketing_keywords = self.config.get('marketing_keywords', [])
        marketing_score = sum(1 for keyword in marketing_keywords if keyword in combined_text)
        
        if email.has_unsubscribe or marketing_score >= 2:
            return TriageDecision(
                email_id=email.id,
                action="trash",
                confidence=0.7 + (marketing_score * 0.1),
                reasoning="Appears to be marketing/newsletter content"
            )
        
        # Default to revisit for uncertain cases
        return TriageDecision(
            email_id=email.id,
            action="revisit",
            confidence=0.5,
            reasoning="Uncertain classification, needs human review"
        )
    
    def get_matching_preferences(self, email: EmailItem) -> List[UserPreference]:
        """Get preferences that match this email"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        preferences = []
        
        # Check sender exact match
        cursor.execute(
            "SELECT * FROM preferences WHERE pattern_type='sender' AND pattern_value=?",
            (email.sender,)
        )
        for row in cursor.fetchall():
            preferences.append(self._row_to_preference(row))
        
        # Check domain match
        cursor.execute(
            "SELECT * FROM preferences WHERE pattern_type='domain' AND pattern_value=?",
            (email.sender_domain,)
        )
        for row in cursor.fetchall():
            preferences.append(self._row_to_preference(row))
        
        # Check subject keywords
        subject_words = email.subject.lower().split()
        for word in subject_words:
            cursor.execute(
                "SELECT * FROM preferences WHERE pattern_type='subject_keyword' AND pattern_value=?",
                (word,)
            )
            for row in cursor.fetchall():
                preferences.append(self._row_to_preference(row))
        
        conn.close()
        return preferences
    
    def _row_to_preference(self, row) -> UserPreference:
        """Convert database row to UserPreference"""
        return UserPreference(
            pattern_type=row[1],
            pattern_value=row[2],
            action=row[3],
            confidence=row[4],
            created_at=datetime.fromisoformat(row[5]),
            usage_count=row[6]
        )
    
    def get_learned_preferences(self) -> List[UserPreference]:
        """Get all learned preferences, sorted by confidence"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT * FROM preferences ORDER BY confidence DESC, usage_count DESC"
        )
        
        preferences = [self._row_to_preference(row) for row in cursor.fetchall()]
        conn.close()
        return preferences
    
    def learn_from_decision(self, email: EmailItem, decision: TriageDecision, user_confirmed: bool):
        """Learn from user decision to improve future classifications"""
        if not user_confirmed:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Record the decision
        cursor.execute('''
            INSERT INTO decisions (email_id, sender, subject, action, reasoning, was_auto_decided)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (email.id, email.sender, email.subject, decision.action, 
              decision.reasoning, decision.confidence > self.config.get('auto_decide_threshold', 0.85)))
        
        # Learn patterns
        patterns_to_learn = [
            ('sender', email.sender),
            ('domain', email.sender_domain),
        ]
        
        # Learn from subject keywords
        subject_words = [word.lower() for word in email.subject.split() if len(word) > 3]
        for word in subject_words[:3]:  # Top 3 meaningful words
            patterns_to_learn.append(('subject_keyword', word))
        
        for pattern_type, pattern_value in patterns_to_learn:
            cursor.execute('''
                INSERT OR REPLACE INTO preferences 
                (pattern_type, pattern_value, action, confidence, usage_count)
                VALUES (?, ?, ?, 
                    COALESCE((SELECT confidence FROM preferences 
                             WHERE pattern_type=? AND pattern_value=? AND action=?) + 0.1, 0.6),
                    COALESCE((SELECT usage_count FROM preferences 
                             WHERE pattern_type=? AND pattern_value=? AND action=?) + 1, 1)
                )
            ''', (pattern_type, pattern_value, decision.action,
                  pattern_type, pattern_value, decision.action,
                  pattern_type, pattern_value, decision.action))
        
        conn.commit()
        conn.close()
    
    def process_batch(self, emails: List[EmailItem]) -> List[Tuple[EmailItem, TriageDecision]]:
        """Process a batch of emails and return decisions"""
        results = []
        auto_decisions = []
        manual_decisions = []
        
        print(f"\n📧 Processing {len(emails)} emails...")
        
        for email in emails:
            decision = self.classify_email_ai(email)
            
            if decision.confidence >= self.config.get('auto_decide_threshold', 0.85):
                auto_decisions.append((email, decision))
            else:
                manual_decisions.append((email, decision))
        
        # Handle auto-decisions
        if auto_decisions:
            # Create summary by action and confidence
            action_summary = {}
            confidence_levels = {"high": 0, "medium": 0}
            
            for email, decision in auto_decisions:
                action = decision.action
                if action not in action_summary:
                    action_summary[action] = []
                action_summary[action].append((email, decision))
                
                # Count confidence levels
                if decision.confidence >= 0.95:
                    confidence_levels["high"] += 1
                else:
                    confidence_levels["medium"] += 1
            
            print(f"\n🤖 {len(auto_decisions)} emails ready for auto-processing:")
            
            # Show summary by action
            action_icons = {"trash": "🗑️", "revisit": "⏰", "action_needed": "⚡"}
            for action, items in action_summary.items():
                action_name = action.replace('_', ' ').title()
                icon = action_icons.get(action, "📧")
                print(f"  {icon} {len(items)} emails → {action_name}")
            
            # Show confidence breakdown
            conf_msg = []
            if confidence_levels["high"] > 0:
                conf_msg.append(f"{confidence_levels['high']} above 95% confident")
            if confidence_levels["medium"] > 0:
                conf_msg.append(f"{confidence_levels['medium']} above 85% confident")
            
            if conf_msg:
                print(f"  📊 Confidence: {', '.join(conf_msg)}")
            
            if self.confirm_batch_action("Apply these automatic decisions?"):
                for email, decision in auto_decisions:
                    self.learn_from_decision(email, decision, True)
                    self.session_stats[decision.action] += 1
                    self.session_stats['auto_decided'] += 1
                results.extend(auto_decisions)
            else:
                manual_decisions.extend(auto_decisions)
        
        # Handle manual decisions
        for email, decision in manual_decisions:
            confirmed_decision = self.get_user_decision(email, decision)
            if confirmed_decision:
                self.learn_from_decision(email, confirmed_decision, True)
                self.session_stats[confirmed_decision.action] += 1
                results.append((email, confirmed_decision))
        
        self.session_stats['processed'] = len(results)
        return results
    
    def get_user_decision(self, email: EmailItem, suggested_decision: TriageDecision) -> Optional[TriageDecision]:
        """Get user decision for an email"""
        print(f"\n" + "="*80)
        print(f"📧 Email from: {email.sender}")
        print(f"📝 Subject: {email.subject}")
        print(f"📄 Preview: {email.snippet[:200]}...")
        if email.has_unsubscribe:
            print(f"🔗 Has unsubscribe link")
        print(f"🤖 AI suggests: {suggested_decision.action} (confidence: {suggested_decision.confidence:.2f})")
        print(f"💭 Reasoning: {suggested_decision.reasoning}")
        
        # Start text-to-speech with AI suggestion first
        if self.config.get('enable_tts', True):
            self._speak_email_details_staged(email, suggested_decision)
        
        while True:
            print(f"\nChoose action:")
            print(f"")
            print(f"  [9] 🗑️  Trash/Archive")
            print(f"")
            print(f"  [5] ⏰ Revisit Later") 
            print(f"")
            print(f"  [1] ⚡ Action Needed")
            print(f"")
            print(f"  [Space] ❌ Reject AI suggestion")
            print(f"  [Enter] ✅ Accept AI suggestion ({suggested_decision.action})")
            print(f"")
            print(f"  [0] 🚫 Opt-out (Data Erasure Request)")
            print(f"  [-] 📚 Mark as read & archive all from sender (same subject)")
            print(f"")
            print(f"  [q] 🚪 Quit session")
            print(f"\nPress any key (no Enter needed)...")
            
            # Get single keypress
            choice = getch()
            
            # Handle special keys
            if ord(choice) == 13:  # Enter key
                choice = 'enter'
            elif ord(choice) == 32:  # Space key
                choice = 'space'
            elif choice == '0':  # Numpad 0 or regular 0
                choice = 'opt_out'
            elif choice == '-':  # Numpad minus or regular minus
                choice = 'bulk_archive'
            else:
                choice = choice.lower()
            
            print(f"Choice: {choice}")  # Show what was pressed
            
            # Interrupt any ongoing speech when user makes a decision
            if self.tts_manager and hasattr(self.tts_manager, 'interrupt_current_speech'):
                self.tts_manager.interrupt_current_speech()
            
            if choice == 'enter':
                return suggested_decision
            elif choice == '9':
                return TriageDecision(email.id, 'trash', 1.0, 'User decision')
            elif choice == '5':
                return TriageDecision(email.id, 'revisit', 1.0, 'User decision')
            elif choice == '1':
                return TriageDecision(email.id, 'action_needed', 1.0, 'User decision')
            elif choice == 'space':
                # Reject AI suggestion, continue to manual review
                continue
            elif choice == 'opt_out':
                return self._handle_opt_out(email)
            elif choice == 'bulk_archive':
                return self._handle_bulk_archive(email)
            elif choice == 'q':
                # Interrupt speech before quitting
                if self.tts_manager and hasattr(self.tts_manager, 'interrupt_current_speech'):
                    self.tts_manager.interrupt_current_speech()
                self.print_session_stats()
                exit(0)
            else:
                print(f"Invalid choice '{choice}'. Please try again.")
    
    def _handle_opt_out(self, email: EmailItem) -> TriageDecision:
        """Handle opt-out request for an email"""
        if not self.opt_out_manager:
            print("⚠️  Opt-out manager not available")
            return TriageDecision(email.id, 'trash', 1.0, 'Opt-out requested but unavailable')
        
        print(f"\n🚫 Processing opt-out request for: {email.sender}")
        
        # Record the opt-out request
        opt_out_info = self.opt_out_manager.record_opt_out_request(email.sender)
        
        # Generate data erasure draft
        draft = self.opt_out_manager.generate_data_erasure_draft(email.sender, email.subject)
        
        print(f"📝 Data erasure request recorded:")
        print(f"   Domain: {opt_out_info['domain']}")
        print(f"   Request count: {opt_out_info['request_count']}")
        
        if opt_out_info['is_repeat_offender']:
            print(f"⚠️  REPEAT OFFENDER - Will mark as SPAM")
            action = 'spam'
            reasoning = f"Repeat offender opt-out (request #{opt_out_info['request_count']})"
        else:
            print(f"📧 First-time opt-out - Will archive after draft creation")
            action = 'opt_out'
            reasoning = f"Data erasure request generated (request #{opt_out_info['request_count']})"
        
        # Store draft info for later processing
        draft_info = {
            'draft': draft,
            'is_repeat_offender': opt_out_info['is_repeat_offender']
        }
        
        return TriageDecision(
            email_id=email.id,
            action=action,
            confidence=1.0,
            reasoning=reasoning,
            suggested_rule=f"opt_out_data:{str(draft_info)}"
        )
    
    def _handle_bulk_archive(self, email: EmailItem) -> TriageDecision:
        """Handle bulk archive request for all emails from sender with same subject"""
        print(f"\n📚 Processing bulk archive for:")
        print(f"   Sender: {email.sender}")
        print(f"   Subject: {email.subject}")
        
        # Store the search criteria for the Gmail client to handle
        bulk_info = {
            'sender': email.sender,
            'subject': email.subject,
            'current_email_id': email.id
        }
        
        print(f"⚠️  This will mark as read and archive ALL emails from this sender with the same subject")
        print(f"   (Only single email threads, no conversations)")
        
        return TriageDecision(
            email_id=email.id,
            action='bulk_archive',
            confidence=1.0,
            reasoning=f"Bulk archive requested for sender: {email.sender}",
            suggested_rule=f"bulk_archive_data:{str(bulk_info)}"
        )
    
    def confirm_batch_action(self, message: str) -> bool:
        """Get yes/no confirmation from user"""
        while True:
            print(f"{message} [y/n] (single keypress): ", end='', flush=True)
            choice = getch().lower()
            print(choice)  # Echo the choice
            
            if choice in ['y']:
                return True
            elif choice in ['n']:
                return False
            else:
                print(f"Invalid choice '{choice}'. Please press 'y' or 'n'")
    
    def send_unsubscribe_request(self, email: EmailItem) -> bool:
        """Send unsubscribe request if available"""
        if not email.has_unsubscribe or not email.unsubscribe_link:
            return False
        
        if not HAS_REQUESTS:
            print("⚠️  Requests library not available for unsubscribe automation")
            return False
        
        # Check if domain is whitelisted (don't auto-unsubscribe from important services)
        whitelist = self.config.get('unsubscribe_domains_whitelist', [])
        if any(domain in email.sender_domain for domain in whitelist):
            print(f"⚠️  Skipping auto-unsubscribe for whitelisted domain: {email.sender_domain}")
            return False
        
        try:
            # Simple GET request to unsubscribe link
            response = requests.get(email.unsubscribe_link, timeout=10)
            if response.status_code == 200:
                print(f"✅ Unsubscribe request sent to {email.sender_domain}")
                return True
            else:
                print(f"⚠️  Unsubscribe request failed: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"⚠️  Unsubscribe request failed: {e}")
            return False
    
    def print_session_stats(self):
        """Print session statistics"""
        stats = self.session_stats
        print(f"\n" + "="*50)
        print(f"📊 SESSION STATISTICS")
        print(f"="*50)
        print(f"📧 Total processed: {stats['processed']}")
        print(f"🗑️  Trash/Archive: {stats['trash']}")
        print(f"⏰ Revisit later: {stats['revisit']}")
        print(f"⚡ Action needed: {stats['action_needed']}")
        print(f"🤖 Auto-decided: {stats['auto_decided']}")
        
        if stats['processed'] > 0:
            auto_rate = (stats['auto_decided'] / stats['processed']) * 100
            print(f"🎯 Automation rate: {auto_rate:.1f}%")


def main():
    """Main function - directs user to use gmail_connector.py"""
    print("🚀 Email Triage System")
    print("="*50)
    print("This is the core triage engine.")
    print("To process real emails, use:")
    print("  python gmail_oauth_client.py")
    print()
    print("For setup help:")
    print("  cat docs/gmail_oauth_setup.md")


if __name__ == "__main__":
    main()
