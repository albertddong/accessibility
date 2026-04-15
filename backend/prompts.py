ANALYZE_PDF_PROMPT = """Analyze this PDF and identify all tables and figures. Return your response as a JSON object with the following structure:

{
  "title": "The title of the PDF document",
  "items": [
    {
      "type": "figure" or "table",
      "number": 1,
      "page": 1,
      "title": "Brief title describing the figure/table",
      "description": "Detailed description of what the figure/table shows",
      "confidence": 0.0,
      "needs_review": false,
      "review_reason": "Why this needs instructor/LD review",
      "table_data": [
        ["Header 1", "Header 2", "Header 3"],
        ["Row 1 Col 1", "Row 1 Col 2", "Row 1 Col 3"],
        ["Row 2 Col 1", "Row 2 Col 2", "Row 2 Col 3"]
      ]
    }
  ]
}

Important:
- Return ONLY valid JSON, no additional text before or after
- Include all figures and tables you find
- Number them sequentially by type (Figure 1, Figure 2, etc. and Table 1, Table 2, etc.)
- Include the 1-indexed page number for each item in "page"
- Include a confidence score 0-1 and set needs_review=true for low-confidence or complex items; add a brief review_reason when needs_review is true
- Provide clear, descriptive titles and detailed descriptions
- For tables: Include "table_data" field with the actual table content as a 2D array (rows x columns)
- For tables: First row should be headers if the table has headers
- For figures: Omit the "table_data" field or set it to null"""
