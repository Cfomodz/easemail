#!/usr/bin/env python3
"""
Email Triage System Launcher
Simple launcher script with menu options
"""

import sys
import os
import termios
import tty
from pathlib import Path

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
            return input("Press key: ").strip()

def check_setup():
    """Check if system is set up"""
    data_dir = Path("./triage_data")
    config_file = data_dir / "config.json"
    db_file = data_dir / "preferences.db"
    
    if not data_dir.exists() or not config_file.exists() or not db_file.exists():
        print("⚠️  System not set up. Running setup...")
        os.system("python setup.py")
        return False
    return True

def show_menu():
    """Show main menu"""
    print("\n" + "="*60)
    print("📧 EMAIL TRIAGE SYSTEM")
    print("="*60)
    print("1. 🚀 Run Gmail Triage (OAuth integration)")
    print("2. ⚙️  Setup/Configuration")
    print("3. 📊 View Statistics")
    print("4. 🔧 Manage Preferences")
    print("5. 🧠 Smart Batching Settings")
    print("6. ❓ Help")
    print("7. 🚪 Exit")
    print("="*60)

def run_gmail_triage():
    """Run Gmail triage"""
    print("🚀 Starting Gmail Triage...")
    try:
        from gmail_oauth_client import SimpleGmailTriageConnector
        connector = SimpleGmailTriageConnector()
        
        # Get default batch size from config
        config = connector.triage_system.config
        default_batch_size = config.get('batch_size', 5)
        default_fetch_size = config.get('fetch_batch_size', 20)
        smart_batching = config.get('enable_smart_batching', True)
        
        print(f"📧 Current settings:")
        print(f"  • Process batch size: {default_batch_size}")
        print(f"  • Fetch batch size: {default_fetch_size}")
        print(f"  • Smart batching: {'✅ Enabled' if smart_batching else '❌ Disabled'}")
        print()
        
        batch_size_input = input(f"Process batch size (default {default_batch_size}): ").strip()
        batch_size = int(batch_size_input) if batch_size_input else default_batch_size
        
        connector.run_triage_session(batch_size)
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all dependencies are installed: pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ Error: {e}")

def run_setup():
    """Run setup"""
    print("⚙️  Setup Instructions")
    print("="*50)
    print("1. 📋 Copy triage_data/config.json.example to triage_data/config.json")
    print("2. 🔑 Add your API keys to config.json:")
    print("   - OpenAI API key")
    print("   - ElevenLabs API key (optional)")
    print("3. 📧 Set up Gmail OAuth (see docs/gmail_oauth_setup.md)")
    print("4. 🚀 Run: python gmail_oauth_client.py")
    print()
    print("📚 For detailed instructions, see README.md")

def view_stats():
    """View statistics"""
    print("📊 Statistics")
    try:
        from email_triage_system import EmailTriageSystem
        import sqlite3
        
        triage = EmailTriageSystem()
        conn = sqlite3.connect(triage.db_path)
        cursor = conn.cursor()
        
        # Decision stats
        cursor.execute("SELECT action, COUNT(*) FROM decisions GROUP BY action")
        decisions = cursor.fetchall()
        
        print("\n📈 Decision History:")
        for action, count in decisions:
            print(f"  {action}: {count}")
        
        # Preference stats
        cursor.execute("SELECT COUNT(*) FROM preferences")
        pref_count = cursor.fetchone()[0]
        print(f"\n🧠 Learned Preferences: {pref_count}")
        
        # Top preferences
        cursor.execute("""
            SELECT pattern_type, pattern_value, action, confidence, usage_count 
            FROM preferences 
            ORDER BY confidence DESC, usage_count DESC 
            LIMIT 10
        """)
        
        print("\n🎯 Top Learned Rules:")
        for row in cursor.fetchall():
            pattern_type, pattern_value, action, confidence, usage_count = row
            print(f"  {pattern_type}:{pattern_value} → {action} (confidence: {confidence:.2f}, used: {usage_count}x)")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error loading stats: {e}")

def manage_preferences():
    """Manage preferences"""
    print("🔧 Preference Management")
    print("1. View all preferences")
    print("2. Add manual preference")
    print("3. Delete preference")
    print("4. Back to main menu")
    
    choice = input("Choice: ").strip()
    
    if choice == "1":
        view_all_preferences()
    elif choice == "2":
        add_manual_preference()
    elif choice == "3":
        delete_preference()

def view_all_preferences():
    """View all preferences"""
    try:
        from email_triage_system import EmailTriageSystem
        import sqlite3
        
        triage = EmailTriageSystem()
        conn = sqlite3.connect(triage.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, pattern_type, pattern_value, action, confidence, usage_count 
            FROM preferences 
            ORDER BY confidence DESC
        """)
        
        print("\n📋 All Preferences:")
        for row in cursor.fetchall():
            id_, pattern_type, pattern_value, action, confidence, usage_count = row
            print(f"  [{id_}] {pattern_type}:{pattern_value} → {action} (conf: {confidence:.2f}, used: {usage_count}x)")
        
        conn.close()
    except Exception as e:
        print(f"❌ Error: {e}")

def add_manual_preference():
    """Add manual preference"""
    print("\n➕ Add Manual Preference")
    
    pattern_type = input("Pattern type (sender/domain/subject_keyword): ").strip()
    if pattern_type not in ['sender', 'domain', 'subject_keyword']:
        print("❌ Invalid pattern type")
        return
    
    pattern_value = input("Pattern value: ").strip()
    if not pattern_value:
        print("❌ Pattern value required")
        return
    
    action = input("Action (trash/revisit/action_needed): ").strip()
    if action not in ['trash', 'revisit', 'action_needed']:
        print("❌ Invalid action")
        return
    
    try:
        confidence = float(input("Confidence (0.0-1.0, default 0.8): ") or "0.8")
        if not 0 <= confidence <= 1:
            print("❌ Confidence must be between 0 and 1")
            return
    except ValueError:
        print("❌ Invalid confidence value")
        return
    
    try:
        from email_triage_system import EmailTriageSystem
        import sqlite3
        
        triage = EmailTriageSystem()
        conn = sqlite3.connect(triage.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO preferences 
            (pattern_type, pattern_value, action, confidence, usage_count)
            VALUES (?, ?, ?, ?, 0)
        """, (pattern_type, pattern_value, action, confidence))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Added preference: {pattern_type}:{pattern_value} → {action}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def delete_preference():
    """Delete a preference"""
    try:
        from email_triage_system import EmailTriageSystem
        import sqlite3
        
        triage = EmailTriageSystem()
        conn = sqlite3.connect(triage.db_path)
        cursor = conn.cursor()
        
        # Show all preferences
        cursor.execute("""
            SELECT id, pattern_type, pattern_value, action, confidence, usage_count 
            FROM preferences 
            ORDER BY id
        """)
        
        preferences = cursor.fetchall()
        if not preferences:
            print("📭 No preferences found")
            conn.close()
            return
        
        print("\n📋 Current Preferences:")
        for row in preferences:
            id_, pattern_type, pattern_value, action, confidence, usage_count = row
            print(f"  [{id_}] {pattern_type}:{pattern_value} → {action} (conf: {confidence:.2f}, used: {usage_count}x)")
        
        pref_id = input("\nEnter preference ID to delete: ").strip()
        if not pref_id.isdigit():
            print("❌ Invalid ID")
            conn.close()
            return
        
        # Delete preference
        cursor.execute("DELETE FROM preferences WHERE id = ?", (int(pref_id),))
        
        if cursor.rowcount > 0:
            conn.commit()
            print(f"✅ Deleted preference {pref_id}")
        else:
            print(f"❌ Preference {pref_id} not found")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

def manage_smart_batching():
    """Manage smart batching settings"""
    print("🧠 Smart Batching Settings")
    print("="*50)
    
    try:
        import json
        from pathlib import Path
        
        config_file = Path("./triage_data/config.json")
        if not config_file.exists():
            print("❌ Config file not found. Please run setup first.")
            return
        
        # Load current config
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Show current settings
        print("📧 Current Smart Batching Settings:")
        print(f"  • Process batch size: {config.get('batch_size', 5)}")
        print(f"  • Fetch batch size: {config.get('fetch_batch_size', 20)}")
        print(f"  • Smart batching enabled: {config.get('enable_smart_batching', True)}")
        print(f"  • Background preprocessing: {config.get('preprocess_next_batch', True)}")
        print()
        
        # Menu options
        print("Options:")
        print("1. Toggle smart batching on/off")
        print("2. Change process batch size")
        print("3. Change fetch batch size")
        print("4. Toggle background preprocessing")
        print("5. Back to main menu")
        
        choice = input("Choice: ").strip()
        
        if choice == "1":
            current = config.get('enable_smart_batching', True)
            config['enable_smart_batching'] = not current
            status = "enabled" if not current else "disabled"
            print(f"✅ Smart batching {status}")
            
        elif choice == "2":
            current = config.get('batch_size', 5)
            new_size = input(f"New process batch size (current: {current}): ").strip()
            if new_size.isdigit() and int(new_size) > 0:
                config['batch_size'] = int(new_size)
                print(f"✅ Process batch size set to {new_size}")
            else:
                print("❌ Invalid batch size")
                return
                
        elif choice == "3":
            current = config.get('fetch_batch_size', 20)
            new_size = input(f"New fetch batch size (current: {current}): ").strip()
            if new_size.isdigit() and int(new_size) > 0:
                config['fetch_batch_size'] = int(new_size)
                print(f"✅ Fetch batch size set to {new_size}")
            else:
                print("❌ Invalid batch size")
                return
                
        elif choice == "4":
            current = config.get('preprocess_next_batch', True)
            config['preprocess_next_batch'] = not current
            status = "enabled" if not current else "disabled"
            print(f"✅ Background preprocessing {status}")
            
        elif choice == "5":
            return
        else:
            print("❌ Invalid choice")
            return
        
        # Save updated config
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=4)
        
        print("💾 Settings saved!")
        
    except Exception as e:
        print(f"❌ Error managing settings: {e}")

def show_help():
    """Show help"""
    print("\n❓ HELP")
    print("="*40)
    print("📧 Email Triage System helps you process large volumes of emails efficiently.")
    print()
    print("🎯 How it works:")
    print("1. Continuously fetches emails from your inbox")
    print("2. AI classifies each email into 3 categories")
    print("3. High-confidence decisions are auto-applied")
    print("4. Uncertain cases require your yes/no decision")
    print("5. System learns from your choices")
    print("6. Automatically fetches more emails when done")
    print("7. Continues until you press Ctrl+C or no more emails")
    print()
    print("🧠 Smart Batching:")
    print("- Fetches large batches (default: 20 emails)")
    print("- Processes in smaller chunks (default: 5 emails)")
    print("- Pre-processes next batch while you work")
    print("- Seamless transition between batches")
    print()
    print("🔧 Setup Requirements:")
    print("- OpenAI API key (optional, improves accuracy)")
    print("- Gmail OAuth credentials (see docs/gmail_oauth_setup.md)")
    print("- Python dependencies (see requirements.txt)")
    print()
    print("📚 For detailed documentation, see README.md")

def main():
    """Main launcher"""
    print("🚀 Email Triage System Launcher")
    
    # Check if setup is complete
    if not check_setup():
        print("Setup complete! You can now use the system.")
    
    while True:
        show_menu()
        choice = input("\nEnter your choice (1-6): ").strip()
        
        if choice == "1":
            run_gmail_triage()
        elif choice == "2":
            run_setup()
        elif choice == "3":
            view_stats()
        elif choice == "4":
            manage_preferences()
        elif choice == "5":
            manage_smart_batching()
        elif choice == "6":
            show_help()
        elif choice == "7":
            print("👋 Goodbye!")
            sys.exit(0)
        else:
            print("❌ Invalid choice. Please try again.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()
