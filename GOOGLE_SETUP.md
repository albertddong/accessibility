# Google API Setup Guide

This guide will walk you through setting up Google API credentials to enable Google Docs creation.

## Prerequisites

- A Google account
- Access to Google Cloud Console

## Step-by-Step Setup

### 1. Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown at the top of the page
3. Click "NEW PROJECT"
4. Enter a project name (e.g., "PDF Analyzer")
5. Click "CREATE"

### 2. Enable Required APIs

1. In the Google Cloud Console, make sure your new project is selected
2. Go to **APIs & Services** > **Library**
3. Search for and enable the following APIs:
   - **Google Docs API** - Click "ENABLE"
   - **Google Drive API** - Click "ENABLE"

### 3. Create OAuth 2.0 Credentials

1. Go to **APIs & Services** > **Credentials**
2. Click **+ CREATE CREDENTIALS** at the top
3. Select **OAuth client ID**
4. If prompted to configure the consent screen:
   - Click **CONFIGURE CONSENT SCREEN**
   - Select **External** user type
   - Click **CREATE**
   - Fill in the required fields:
     - App name: "PDF Analyzer"
     - User support email: Your email
     - Developer contact information: Your email
   - Click **SAVE AND CONTINUE**
   - Skip the Scopes section (click **SAVE AND CONTINUE**)
   - Add your email as a test user
   - Click **SAVE AND CONTINUE**
   - Click **BACK TO DASHBOARD**

5. Return to **Credentials** and click **+ CREATE CREDENTIALS** > **OAuth client ID**
6. Select **Desktop app** as the application type
7. Enter a name (e.g., "PDF Analyzer Desktop")
8. Click **CREATE**

### 4. Download Credentials

1. After creating the OAuth client ID, a dialog will appear with your credentials
2. Click **DOWNLOAD JSON**
3. Save the downloaded file as `credentials.json` in your project directory:
   ```
   /Users/adeDd/Documents/Coding/accessibility-rem/credentials.json
   ```

### 5. First-Time Authentication

When you run the application and click "Create Google Doc" for the first time:

1. A browser window will open asking you to sign in to Google
2. Select your Google account
3. You may see a warning that the app isn't verified - this is normal for development
4. Click **Advanced** > **Go to [Your App Name] (unsafe)**
5. Grant the requested permissions:
   - See, edit, create, and delete all your Google Docs documents
   - See, edit, create, and delete only the specific Google Drive files you use with this app
6. Click **Continue**

The app will save your authentication token in `token.pickle`, so you won't need to authenticate again unless you revoke access.

## File Structure

After setup, your project directory should contain:

```
accessibility-rem/
├── app.py
├── requirements.txt
├── credentials.json          # Your OAuth credentials (DO NOT COMMIT)
├── token.pickle             # Auto-generated after first auth (DO NOT COMMIT)
├── .env                     # Your API keys (DO NOT COMMIT)
└── GOOGLE_SETUP.md          # This file
```

## Security Notes

⚠️ **IMPORTANT**: Never commit these files to version control:
- `credentials.json` - Contains your OAuth client secrets
- `token.pickle` - Contains your access tokens
- `.env` - Contains your API keys

Add them to your `.gitignore`:
```
credentials.json
token.pickle
.env
token.json
```

## Troubleshooting

### "Access blocked: This app's request is invalid"
- Make sure you've enabled both Google Docs API and Google Drive API
- Verify your OAuth consent screen is configured

### "The app is not verified"
- This is normal for development apps
- Click "Advanced" and proceed to your app

### "Invalid grant" error
- Delete `token.pickle` and re-authenticate
- Make sure your system clock is correct

### Port 8080 already in use
- The OAuth flow uses port 8080 by default
- Close any applications using this port or modify the port in `app.py`

## Testing

To test that everything is set up correctly:

1. Run the Streamlit app: `streamlit run app.py`
2. Upload a PDF and analyze it
3. Click "Create Google Doc"
4. Check your Google Drive for the newly created document

## Additional Resources

- [Google Docs API Documentation](https://developers.google.com/docs/api)
- [Google Drive API Documentation](https://developers.google.com/drive/api)
- [OAuth 2.0 for Desktop Apps](https://developers.google.com/identity/protocols/oauth2/native-app)
