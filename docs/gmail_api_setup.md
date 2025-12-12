# Gmail API Setup Guide

This guide will walk you through setting up Gmail API access for the Email Digest Agent.

## Step 1: Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown at the top
3. Click "New Project"
4. Enter a project name (e.g., "Email Digest Agent")
5. Click "Create"

## Step 2: Enable Gmail API

1. In your project, navigate to "APIs & Services" > "Library"
2. Search for "Gmail API"
3. Click on "Gmail API"
4. Click "Enable"

## Step 3: Create OAuth 2.0 Credentials

1. Navigate to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. If prompted, configure the OAuth consent screen:
   - User Type: External (or Internal if using Google Workspace)
   - App name: "Email Digest Agent"
   - User support email: Your email
   - Developer contact: Your email
   - Click "Save and Continue"
   - Scopes: Skip for now (the app will request scopes at runtime)
   - Test users: Add your email address
   - Click "Save and Continue"
4. Back at "Create OAuth client ID":
   - Application type: "Desktop app"
   - Name: "Email Digest Agent Desktop"
   - Click "Create"
5. Download the credentials JSON file
6. Rename it to `credentials.json`
7. Place it in the project root directory: `/Users/terresapan/Documents/LangGraph Agents/emailagent/credentials.json`

## Step 4: First-Time Authentication

The first time you run the agent, it will open a browser window for authentication:

```bash
uv run main.py --dry-run
```

1. A browser window will open
2. Select your Google account
3. Click "Continue" when warned about the app not being verified (if applicable)
4. Grant the requested permissions:
   - Read emails
   - Modify emails (mark as read, apply labels)
   - Create drafts
5. The authentication will complete and a `token.json` file will be created
6. Future runs will use `token.json` automatically

## Security Notes

- **Never commit `credentials.json` or `token.json` to version control**
- These files are already in `.gitignore`
- `credentials.json` allows anyone to authenticate as your app
- `token.json` contains your personal access token

## Troubleshooting

### "Access blocked: This app hasn't been verified"

If you see this error:
1. Click "Advanced"
2. Click "Go to Email Digest Agent (unsafe)"
3. Grant permissions

This happens because the app isn't verified by Google. Since it's for personal use, this is safe.

### Token Expired

If you get authentication errors after some time:
```bash
rm token.json
uv run main.py --dry-run
```

This will trigger a fresh authentication flow.

### Permission Errors

Ensure the OAuth consent screen has the correct scopes. The agent requires:
- `https://www.googleapis.com/auth/gmail.readonly`
- `https://www.googleapis.com/auth/gmail.modify`
- `https://www.googleapis.com/auth/gmail.labels`
