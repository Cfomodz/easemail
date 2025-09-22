# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-XX

### Added
- **AI-Powered Email Classification**: Automatic triage using OpenAI GPT-4
- **Voice Integration**: ElevenLabs Flash v2.5 text-to-speech with streaming and interruption
- **Single-Keypress Interface**: Efficient decision making without Enter key
- **Batch Processing**: Process emails in configurable batches (default: 5)
- **Opt-Out System**: GDPR-compliant data erasure requests with repeat offender tracking
- **Bulk Archive**: Archive all emails from sender with same subject (single threads only)
- **Preference Learning**: SQLite database for storing user decisions and creating rules
- **Gmail Integration**: Direct OAuth integration with Gmail API
- **Smart Filtering**: Excludes already-triaged emails from subsequent fetches
- **Confidence Scoring**: AI suggestions with confidence levels and detailed summaries
- **Staged Speech**: AI suggestion spoken first, then email details, with interruption support

### Features
- **Three-Pile Sorting**: Trash/Archive, Revisit Later, Action Needed
- **Keyboard Layout**: Intuitive numpad-based controls (9, 5, 1, Space, Enter, 0, -)
- **Auto-Processing**: Batch approval for high-confidence decisions
- **Voice Controls**: Immediate interruption and async playback
- **Repeat Offender Detection**: Automatic spam marking for persistent senders
- **Thread Detection**: Smart handling of conversation threads vs single emails
- **Configuration Management**: JSON-based configuration with example template

### Technical
- **Python 3.8+** compatibility
- **Gmail API** integration with OAuth2 authentication
- **OpenAI API** for email classification
- **ElevenLabs API** for high-quality text-to-speech
- **SQLite** for preference storage
- **Pygame** for audio playback
- **Cross-platform** support (Linux, macOS, Windows)

### Documentation
- Comprehensive README with quick start guide
- Gmail OAuth setup instructions
- Configuration examples and options
- Project structure documentation
- Contributing guidelines

## [Unreleased]

### Planned
- Web interface for remote management
- Additional TTS providers (Azure, AWS Polly)
- Email templates for common responses
- Integration with other email providers
- Machine learning model fine-tuning
- Mobile app companion
- Team collaboration features
- Advanced filtering rules
- Email analytics and reporting
- Plugin system for extensibility
