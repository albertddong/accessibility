import json
import os
import secrets
from urllib.parse import urlencode

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from backend.config import settings
from backend.schemas import CreateGoogleDocResponse, PdfAnalysis
from backend.services.tables import normalize_table_data


SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive.file",
]

TOKEN_STORE: dict[str, dict] = {}

if settings.allow_insecure_oauth_transport:
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"


def _redirect_uri() -> str:
    return f"{settings.public_backend_url.rstrip('/')}/api/google-auth/callback"


def _build_flow(state: str | None = None) -> Flow:
    flow = Flow.from_client_secrets_file(
        str(settings.google_credentials_path),
        scopes=SCOPES,
        state=state,
    )
    flow.redirect_uri = _redirect_uri()
    return flow


def ensure_session_id(session: dict) -> str:
    session_id = session.get("session_id")
    if not session_id:
        session_id = secrets.token_urlsafe(24)
        session["session_id"] = session_id
    return session_id


def begin_google_oauth(session: dict) -> str | None:
    if not settings.google_credentials_path.exists():
        return None

    flow = _build_flow()
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    session["google_oauth_state"] = state
    ensure_session_id(session)
    return authorization_url


def complete_google_oauth(session: dict, authorization_response: str) -> None:
    expected_state = session.get("google_oauth_state")
    if not expected_state:
        raise ValueError("Missing OAuth state in session.")

    flow = _build_flow(expected_state)
    flow.fetch_token(authorization_response=authorization_response)
    TOKEN_STORE[ensure_session_id(session)] = credentials_to_dict(flow.credentials)
    session["google_connected"] = True
    session.pop("google_oauth_state", None)


def get_google_credentials(session: dict):
    session_id = session.get("session_id")
    if not session_id:
        return None

    stored = TOKEN_STORE.get(session_id)
    if not stored:
        return None

    credentials = Credentials(**stored)
    return credentials


def credentials_to_dict(credentials) -> dict:
    return {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes,
    }


def google_auth_status(session: dict) -> dict:
    return {
        "connected": get_google_credentials(session) is not None,
    }


def build_post_auth_redirect(success: bool, message: str | None = None) -> str:
    params = {"google_auth": "success" if success else "error"}
    if message:
        params["message"] = message
    return f"{settings.frontend_post_auth_url}?{urlencode(params)}"


def create_google_doc(analysis: PdfAnalysis, credentials) -> CreateGoogleDocResponse:
    docs_service = build("docs", "v1", credentials=credentials)
    drive_service = build("drive", "v3", credentials=credentials)

    doc = docs_service.documents().create(body={"title": analysis.title}).execute()
    doc_id = doc["documentId"]
    pending_comments: list[dict] = []
    debug_logs: list[dict] = []

    for item_index, item in enumerate(analysis.items):
        item_type = item.type.capitalize()
        item_number = item.number or (item_index + 1)
        item_title = item.title
        item_description = item.description
        table_was_inserted = False
        table_insert_location = None
        heading_range = None

        doc_snapshot = docs_service.documents().get(documentId=doc_id).execute()
        end_index = doc_snapshot["body"]["content"][-1]["endIndex"]
        current_index = end_index - 1

        requests = []

        if item_index == 0:
            requests.append(
                {
                    "insertText": {
                        "location": {"index": 1},
                        "text": f"{analysis.title}\n",
                    }
                }
            )
            requests.append(
                {
                    "updateParagraphStyle": {
                        "range": {"startIndex": 1, "endIndex": len(analysis.title) + 1},
                        "paragraphStyle": {"namedStyleType": "HEADING_1"},
                        "fields": "namedStyleType",
                    }
                }
            )
            current_index = len(analysis.title) + 2

        heading_text = f"{item_type} {item_number}: {item_title}\n"
        description_text = f"{item_description}\n\n"

        requests.append(
            {
                "insertText": {
                    "location": {"index": current_index},
                    "text": heading_text,
                }
            }
        )

        heading_start = current_index
        heading_end = current_index + len(heading_text) - 1
        heading_range = (heading_start, heading_start + len(heading_text))
        requests.append(
            {
                "updateParagraphStyle": {
                    "range": {"startIndex": heading_start, "endIndex": heading_end},
                    "paragraphStyle": {"namedStyleType": "HEADING_2"},
                    "fields": "namedStyleType",
                }
            }
        )

        current_index += len(heading_text)

        if item.needs_review:
            requests.append(
                {
                    "updateTextStyle": {
                        "range": {"startIndex": heading_range[0], "endIndex": heading_range[1]},
                        "textStyle": {
                            "backgroundColor": {
                                "color": {"rgbColor": {"red": 1.0, "green": 0.95, "blue": 0.6}}
                            }
                        },
                        "fields": "backgroundColor",
                    }
                }
            )

            review_note_parts = ["[Needs review]"]
            if item.page:
                review_note_parts.append(f"Page {item.page}")
            if item.confidence is not None:
                review_note_parts.append(f"Confidence {item.confidence:.2f}")
            if item.review_reason:
                review_note_parts.append(f"Reason: {item.review_reason}")

            review_note_text = " | ".join(review_note_parts) + "\n"
            requests.append(
                {
                    "insertText": {
                        "location": {"index": current_index},
                        "text": review_note_text,
                    }
                }
            )
            requests.append(
                {
                    "updateTextStyle": {
                        "range": {
                            "startIndex": current_index,
                            "endIndex": current_index + len(review_note_text),
                        },
                        "textStyle": {
                            "italic": True,
                            "foregroundColor": {
                                "color": {"rgbColor": {"red": 0.7, "green": 0.0, "blue": 0.0}}
                            },
                        },
                        "fields": "italic,foregroundColor",
                    }
                }
            )
            current_index += len(review_note_text)

        requests.append(
            {
                "insertText": {
                    "location": {"index": current_index},
                    "text": description_text,
                }
            }
        )
        current_index += len(description_text)

        if item.type.lower() == "table" and item.table_data:
            table_data = normalize_table_data(item.table_data)
            if table_data:
                rows = len(table_data)
                cols = len(table_data[0]) if rows > 0 else 0
                if rows > 0 and cols > 0:
                    requests.append(
                        {
                            "insertTable": {
                                "rows": rows,
                                "columns": cols,
                                "location": {"index": current_index},
                            }
                        }
                    )
                    table_was_inserted = True
                    table_insert_location = current_index

        if requests:
            docs_service.documents().batchUpdate(
                documentId=doc_id,
                body={"requests": requests},
            ).execute()

        if table_was_inserted and item.table_data:
            table_data = normalize_table_data(item.table_data)
            if table_data:
                doc_after_insert = docs_service.documents().get(documentId=doc_id).execute()
                candidate_table = None
                min_distance = None
                tables_debug_before = []

                for element in doc_after_insert["body"]["content"]:
                    if "table" not in element:
                        continue

                    start_idx = element.get("startIndex", 0)
                    cell_positions = []
                    for row_index, row in enumerate(element["table"]["tableRows"]):
                        for col_index, cell in enumerate(row["tableCells"]):
                            cell_positions.append(
                                {
                                    "row": row_index,
                                    "col": col_index,
                                    "cell_startIndex": cell.get("startIndex"),
                                    "first_content_startIndex": (
                                        cell["content"][0].get("startIndex", None)
                                        if cell.get("content")
                                        else None
                                    ),
                                }
                            )

                    tables_debug_before.append(
                        {
                            "startIndex": start_idx,
                            "rows": len(element["table"]["tableRows"]),
                            "cols": (
                                len(element["table"]["tableRows"][0]["tableCells"])
                                if element["table"]["tableRows"]
                                else 0
                            ),
                            "cell_positions": cell_positions,
                        }
                    )

                    distance = abs((table_insert_location or start_idx) - start_idx)
                    if min_distance is None or distance < min_distance:
                        min_distance = distance
                        candidate_table = element["table"]

                table_requests = []
                tables_debug_after = []

                if candidate_table:
                    cell_entries = []
                    for row_index, row_data in enumerate(table_data):
                        if row_index >= len(candidate_table["tableRows"]):
                            continue
                        table_row = candidate_table["tableRows"][row_index]
                        for col_index, cell_value in enumerate(row_data):
                            if col_index >= len(table_row["tableCells"]):
                                continue
                            cell = table_row["tableCells"][col_index]
                            cell_start = cell.get("startIndex", 0)
                            cell_end = cell.get("endIndex", cell_start + 1)
                            target_index = cell_start + 1
                            if cell_end is not None and target_index >= cell_end:
                                target_index = max(cell_start, cell_end - 1)
                            cell_text = "" if cell_value is None else str(cell_value)
                            if not cell_text.strip():
                                continue
                            cell_entries.append({"startIndex": target_index, "value": cell_text})

                    cell_entries.sort(key=lambda entry: entry["startIndex"], reverse=True)
                    for entry in cell_entries:
                        table_requests.append(
                            {
                                "insertText": {
                                    "location": {"index": entry["startIndex"]},
                                    "text": entry["value"],
                                }
                            }
                        )

                if table_requests:
                    docs_service.documents().batchUpdate(
                        documentId=doc_id,
                        body={"requests": table_requests},
                    ).execute()

                    doc_after_population = docs_service.documents().get(documentId=doc_id).execute()
                    for element in doc_after_population["body"]["content"]:
                        if "table" not in element:
                            continue
                        cell_positions = []
                        for row_index, row in enumerate(element["table"]["tableRows"]):
                            for col_index, cell in enumerate(row["tableCells"]):
                                cell_positions.append(
                                    {
                                        "row": row_index,
                                        "col": col_index,
                                        "cell_startIndex": cell.get("startIndex"),
                                        "first_content_startIndex": (
                                            cell["content"][0].get("startIndex", None)
                                            if cell.get("content")
                                            else None
                                        ),
                                    }
                                )
                        tables_debug_after.append(
                            {
                                "startIndex": element.get("startIndex", 0),
                                "rows": len(element["table"]["tableRows"]),
                                "cols": (
                                    len(element["table"]["tableRows"][0]["tableCells"])
                                    if element["table"]["tableRows"]
                                    else 0
                                ),
                                "cell_positions": cell_positions,
                            }
                        )

                debug_logs.append(
                    {
                        "item_number": item_number,
                        "item_title": item_title,
                        "table_insert_location": table_insert_location,
                        "table_data": table_data,
                        "tables_before": tables_debug_before,
                        "tables_after": tables_debug_after,
                    }
                )

        if item.needs_review and heading_range:
            comment_parts = []
            if item.page:
                comment_parts.append(f"Page: {item.page}")
            if item.confidence is not None:
                comment_parts.append(f"Confidence: {item.confidence:.2f}")
            if item.review_reason:
                comment_parts.append(f"Reason: {item.review_reason}")
            pending_comments.append(
                {
                    "start": heading_range[0],
                    "end": heading_range[1],
                    "content": " | ".join(comment_parts) if comment_parts else "Needs review",
                }
            )

        if item_index < len(analysis.items) - 1:
            doc_after_item = docs_service.documents().get(documentId=doc_id).execute()
            end_index_after_item = doc_after_item["body"]["content"][-1]["endIndex"]
            docs_service.documents().batchUpdate(
                documentId=doc_id,
                body={
                    "requests": [
                        {
                            "insertPageBreak": {
                                "location": {"index": end_index_after_item - 1}
                            }
                        }
                    ]
                },
            ).execute()

    for comment in pending_comments:
        try:
            drive_service.comments().create(
                fileId=doc_id,
                body={
                    "content": comment["content"],
                    "anchor": json.dumps(
                        {
                            "r": {
                                "segmentId": "",
                                "startIndex": comment["start"],
                                "endIndex": comment["end"],
                            }
                        }
                    ),
                },
                fields="*",
            ).execute()
        except Exception as exc:
            debug_logs.append(
                {
                    "comment_error": str(exc),
                    "comment_payload": comment,
                }
            )

    return CreateGoogleDocResponse(
        document_id=doc_id,
        document_url=f"https://docs.google.com/document/d/{doc_id}/edit",
        debug_logs=debug_logs,
    )
