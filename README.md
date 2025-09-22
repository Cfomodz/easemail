<div align="center">

<img src="docs/easemail.png" alt="easemail" width="400"/>

![GitHub License](https://img.shields.io/github/license/Cfomodz/easemail)
![Discord](https://img.shields.io/discord/425182625032962049)
![GitHub Sponsors](https://img.shields.io/github/sponsors/Cfomodz)

### 🧠 Intelligent Email Triage System

</div>

An AI-powered email management system that helps you process thousands of emails efficiently with smart batch processing, voice feedback, and automated actions.

## ✨ Features

### 🤖 AI-Powered Classification
- **Smart Triage**: Uses OpenAI to automatically classify emails into three categories:
  - 🗑️ **Trash/Archive** - Marketing, newsletters, automated notifications
  - ⏰ **Revisit Later** - Non-urgent items to review when clutter is cleared
  - ⚡ **Action Needed** - Important emails requiring human attention

### 🎯 Batch Processing
- Process emails in small batches (5 at a time) for manageable decision-making
- Auto-process high-confidence decisions with user approval
- Detailed summaries showing confidence levels and action counts

### 🔊 Voice Integration
- **Text-to-Speech**: Uses ElevenLabs Flash v2.5 for high-quality voice output
- **Staged Speech**: AI suggestion spoken first, then email details
- **Instant Interruption**: Stop voice playback immediately when making decisions
- **Streaming Audio**: Real-time audio generation and playback

### ⌨️ Single-Keypress Interface
- **No Enter Required**: Make decisions with single key presses
- **Intuitive Layout**: 
  - `9` - Trash/Archive
  - `5` - Revisit Later  
  - `1` - Action Needed
  - `Enter` - Accept AI suggestion
  - `Space` - Reject AI suggestion
  - `0` - Opt-out (Data erasure request)
  - `-` - Bulk archive all from sender (same subject)

### 🚫 Advanced Opt-Out System
- **Data Erasure Requests**: Automatically generate GDPR-compliant removal requests
- **Repeat Offender Tracking**: Mark as spam if senders ignore previous opt-out requests
- **Smart Detection**: Identifies repeat violations after 7-day grace period

### 📚 Bulk Operations
- **Bulk Archive**: Mark as read and archive all emails from sender with same subject
- **Single Thread Only**: Excludes conversation threads to avoid archiving important replies
- **Smart Subject Matching**: Handles Re:, Fwd: prefixes automatically

### 🧠 Learning System
- **Preference Storage**: Remembers your decisions in SQLite database
- **Rule Generation**: Creates automated rules based on your patterns
- **Confidence Scoring**: Improves suggestions over time

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Gmail account with API access
- OpenAI API key
- ElevenLabs API key (optional, falls back to system TTS)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/email-triage-system.git
   cd email-triage-system
   ```

2. **Set up Python environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure Gmail OAuth**
   - Follow the guide in `docs/gmail_oauth_setup.md`
   - Download `credentials.json` to the project root

4. **Configure API keys**
   ```bash
   cp triage_data/config.json.example triage_data/config.json
   # Edit config.json with your API keys
   ```

5. **Run the system**
   ```bash
   python run_triage.py
   ```

## ⚙️ Configuration

Edit `triage_data/config.json`:

```json
{
  "openai_api_key": "your-openai-key",
  "elevenlabs_api_key": "your-elevenlabs-key",
  "elevenlabs_voice_id": "Z9hrfEHGU3dykHntWvIY",
  "tts_provider": "elevenlabs",
  "confidence_threshold": 0.7,
  "batch_size": 5
}
```

## 🎮 Usage

### Basic Workflow
1. **Start Session**: Run `python run_triage.py`
2. **Review Batch**: System fetches 5 emails and shows AI suggestions
3. **Make Decisions**: Use single keypress to approve, reject, or override
4. **Bulk Actions**: Apply decisions to entire batch or individual emails
5. **Repeat**: Continue until inbox is clean

### Voice Controls
- **Listen**: AI reads suggestion first, then email details
- **Interrupt**: Any keypress stops voice immediately
- **Skip Details**: Make decision during AI suggestion to skip full reading

### Advanced Features
- **Opt-Out**: Generates data erasure request and tracks repeat offenders
- **Bulk Archive**: Archive all emails from sender with same subject (single threads only)
- **Smart Filtering**: Excludes already-triaged emails from future batches

## 📁 Project Structure

```
email-triage-system/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── run_triage.py               # Main launcher
├── email_triage_system.py      # Core triage logic
├── gmail_oauth_client.py       # Gmail API integration
├── tts_manager.py              # Text-to-speech handling
├── opt_out_manager.py          # Opt-out request management
├── triage_data/
│   ├── config.json             # Configuration file
│   ├── preferences.db          # SQLite database (auto-created)
│   └── opt_out_requests.json   # Opt-out tracking (auto-created)
├── docs/
│   └── gmail_oauth_setup.md    # Gmail setup guide
└── tests/
    ├── test_async_tts.py       # TTS testing
    └── test_interruption.py    # Interruption testing
```

## 🔧 Development

### Running Tests
```bash
# Test TTS functionality
python tests/test_async_tts.py

# Test interruption system
python tests/test_interruption.py
```

### Adding New Features
1. Core logic goes in `email_triage_system.py`
2. Gmail operations in `gmail_oauth_client.py`
3. Update configuration in `triage_data/config.json`
4. Add tests in `tests/` directory

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI** for GPT-4 classification
- **ElevenLabs** for high-quality text-to-speech
- **Google** for Gmail API
- **Python Community** for excellent libraries

## 🆘 Support

- **Issues**: Report bugs and request features on GitHub Issues
- **Documentation**: Check `docs/` directory for detailed guides
- **Configuration**: See `triage_data/config.json` for all options

---

**Made with ❤️ for people drowning in email**
