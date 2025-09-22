# Gmail OAuth Setup Guide

## 🎯 Quick Setup (5 minutes)

### 1. Get Gmail API Credentials

1. **Go to Google Cloud Console**: https://console.cloud.google.com/
2. **Create or select a project**
3. **Enable Gmail API**:
   - Go to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click "Enable"

4. **Create OAuth Credentials**:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop application"
   - Name it "Email Triage System"
   - Download the JSON file

5. **Save credentials**:
   - Rename the downloaded file to `credentials.json`
   - Place it in the `/home/toor/life/` directory

### 2. Run the System

```bash
cd /home/toor/life
source venv/bin/activate
python gmail_oauth_client.py
```

The first time you run it:
- A browser window will open
- Sign in to your Google account
- Grant permissions to the Email Triage System
- The system will save your token for future use

### 3. That's it! 

The system will:
- ✅ Connect directly to Gmail (simple and reliable)
- ✅ Use your existing OAuth setup
- ✅ Process emails with AI + voice
- ✅ Apply decisions directly to Gmail
- ✅ Learn your preferences over time

## 🔒 Security Notes

- **Credentials stay local**: Everything runs on your machine
- **No cloud storage**: Tokens and preferences stored locally
- **Standard OAuth**: Uses Google's official authentication
- **Minimal permissions**: Only requests Gmail read/modify access

## 🎛️ Gmail Scopes Used

- `gmail.readonly`: Read your emails
- `gmail.modify`: Add/remove labels, archive emails
- `gmail.labels`: Create triage labels

## 🏷️ Labels Created

The system will automatically create these labels in Gmail:
- `TRIAGE_REVISIT`: For emails to review later
- `TRIAGE_ACTION_NEEDED`: For emails requiring action

## 🔧 Troubleshooting

### "credentials.json not found"
- Make sure you downloaded the OAuth credentials from Google Cloud Console
- Rename the file to exactly `credentials.json`
- Place it in the same directory as the script

### "Access blocked" during OAuth
- Make sure Gmail API is enabled in your Google Cloud project
- Check that OAuth consent screen is configured
- Verify the OAuth client ID is for "Desktop application"

### "Insufficient permissions"
- The system will request the minimum required permissions
- Make sure you grant access to Gmail during the OAuth flow

---

**Simple and straightforward setup!** 🎉
