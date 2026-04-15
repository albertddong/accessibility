# Quick Start Guide

Get up and running in 5 minutes!

## 1. Run the Application

The dependencies are already installed. Start the app:

```bash
source venv/bin/activate
streamlit run app.py
```

The app will open at `http://localhost:8501`

## 2. Analyze a PDF

Your API key is already configured in the `.env` file!

1. Upload a PDF file
2. Click "Analyze PDF"
3. View the extracted tables and figures

That's it! You can use the PDF analysis feature immediately.

**Note:** If you see an API key error, make sure your `.env` file exists with `ANTHROPIC_API_KEY=your_key_here`

## 3. Enable Google Docs Creation (Optional)

To use the "Create Google Doc" feature, you need to set up Google API credentials:

**Follow the detailed guide:** [GOOGLE_SETUP.md](GOOGLE_SETUP.md)

**Short version:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project and enable Google Docs API + Google Drive API
3. Create OAuth 2.0 credentials (Desktop app)
4. Download as `credentials.json` and place in this directory
5. Run the app and click "Create Google Doc"
6. Authenticate on first use

## What Gets Created

When you click "Create Google Doc", the app generates a document like this:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PDF Document Title                    [Heading 1]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Figure 1: Revenue Chart               [Heading 2]
Shows the quarterly revenue growth...  [Normal text]

[Page Break]

Table 1: Sales Data                   [Heading 2]
Contains breakdown of sales by...      [Normal text]

[Page Break]
...
```

## Troubleshooting

### "API Error: credit balance too low"
- Add credits at [Anthropic Console](https://console.anthropic.com/)

### Google Docs button not appearing
- First analyze a PDF, then the button will appear

### "Google credentials not found"
- Follow [GOOGLE_SETUP.md](GOOGLE_SETUP.md) to set up credentials

## Next Steps

- Read the full [README.md](README.md) for more details
- Set up Google Docs integration: [GOOGLE_SETUP.md](GOOGLE_SETUP.md)
- Try analyzing different types of PDFs!
