import base64
import json

import anthropic

from backend.config import settings
from backend.prompts import ANALYZE_PDF_PROMPT
from backend.schemas import AnalyzeResponse, PdfAnalysis, UsageStats


def _extract_json_block(response_text: str) -> str:
    json_text = response_text
    if "```json" in json_text:
        json_text = json_text.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in json_text:
        json_text = json_text.split("```", 1)[1].split("```", 1)[0].strip()
    return json_text


def analyze_pdf_bytes(pdf_bytes: bytes) -> AnalyzeResponse:
    if not settings.anthropic_api_key:
        raise ValueError("Anthropic API key not found. Set ANTHROPIC_API_KEY in your environment.")

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    pdf_base64 = base64.standard_b64encode(pdf_bytes).decode("utf-8")

    message = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_base64,
                        },
                    },
                    {
                        "type": "text",
                        "text": ANALYZE_PDF_PROMPT,
                    },
                ],
            }
        ],
    )

    response_text = message.content[0].text
    parsed = json.loads(_extract_json_block(response_text))
    analysis = PdfAnalysis.model_validate(parsed)

    return AnalyzeResponse(
        analysis=analysis,
        usage=UsageStats(
            input_tokens=getattr(message.usage, "input_tokens", None),
            output_tokens=getattr(message.usage, "output_tokens", None),
            model=message.model,
        ),
    )
