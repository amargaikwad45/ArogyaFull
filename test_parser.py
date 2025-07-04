# test_parser.py

import asyncio
import json
from pathlib import Path

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
# 💡 FIX: No longer importing Blob, just use the core 'types'
from google.genai import types
from dotenv import load_dotenv

# --- 1. Import your custom report_parser_agent ---
from report_parser_agent.agent import report_parser_agent

# Load environment variables
load_dotenv()

# --- 2. Define constants for the test ---
APP_NAME = "test_parser_app"
USER_ID = "test_user"
PDF_FILE_PATH = "/usr/local/google/home/amaragaikwad/temp/med.pdf"

async def main():
    """
    Runs a one-off test to process a PDF with the report_parser_agent.
    """
    print(f"🔬 Starting parser test for: {PDF_FILE_PATH}")

    # --- 3. Setup ADK components for a temporary session ---
    session_service = InMemorySessionService()
    runner = Runner(
        agent=report_parser_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    session = session_service.create_session(app_name=APP_NAME, user_id=USER_ID)
    print(f"Created temporary session: {session.id}")

    # --- 4. Prepare the PDF for the agent ---
    pdf_path = Path(PDF_FILE_PATH)
    if not pdf_path.is_file():
        print(f"❌ ERROR: File not found at '{PDF_FILE_PATH}'. Please check the path.")
        return

    # 💡 --- FIX APPLIED HERE --- 💡
    # Instead of creating a Blob object, we pass a dictionary directly
    # to the 'inline_data' parameter of the Part.
    message_with_pdf = types.Content(
        role="user",
        parts=[
            types.Part(text="Extract the health information from the attached medical report."),
            types.Part(
                inline_data={
                    "mime_type": "application/pdf",
                    "data": pdf_path.read_bytes()
                }
            )
        ]
    )

    # --- 5. Run the agent and process the result ---
    final_json_response = None
    print("\n🚀 Sending PDF to the agent for processing...")

    try:
        async for chunk in runner.run_async(
            user_id=USER_ID, session_id=session.id, new_message=message_with_pdf
        ):
            if chunk.is_final_response and chunk.content and chunk.content.parts:
                json_string = chunk.content.parts[0].text
                final_json_response = json.loads(json_string)
                break

    except Exception as e:
        print(f"❌ An error occurred during the agent run: {e}")
        return

    # --- 6. Display the final extracted JSON ---
    if final_json_response:
        print("\n✅ Extraction successful! Agent returned the following JSON:")
        print("----------------------------------------------------------")
        print(json.dumps(final_json_response, indent=2))
        print("----------------------------------------------------------")
    else:
        print("\n⚠️ Agent did not return a final JSON response.")


if __name__ == "__main__":
    asyncio.run(main())