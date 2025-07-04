# main.py

import asyncio
import json
import uvicorn
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from dotenv import load_dotenv

# --- 1. Import your custom report_parser_agent ---
from report_parser_agent.agent import report_parser_agent, ExpectedOutput

# Load environment variables (e.g., for API keys)
load_dotenv()

# --- 2. Initialize FastAPI App & ADK Runner ---
app = FastAPI(
    title="Medical Report Parser API",
    description="Upload a PDF medical report to extract structured JSON data.",
)

# Use a single, shared session service and runner for the app's lifecycle
session_service = InMemorySessionService()
runner = Runner(
    agent=report_parser_agent,
    app_name="report_parser_app",
    session_service=session_service,
)

# --- 3. Configure CORS ---
# This allows your React frontend (e.g., running on http://localhost:3000)
# to communicate with this backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- 4. Create the Final PDF Processing Endpoint ---
@app.post("/extract/", response_model=ExpectedOutput)
async def extract_data_from_pdf(file: UploadFile = File(...)):
    """
    Accepts a PDF file from a frontend, processes it with the
    report_parser_agent, and returns the structured JSON data.
    """
    # Verify the uploaded file is a PDF
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PDF.")

    print(f"🚀 Received file: {file.filename} ({file.content_type})")

    try:
        # Read the file content directly from the upload
        pdf_bytes = await file.read()

        # Construct the multimodal message for the agent, just like in test_parser.py
        message_with_pdf = types.Content(
            role="user",
            parts=[
                types.Part(text="Extract the health information from the attached medical report."),
                types.Part(
                    inline_data={
                        "mime_type": "application/pdf",
                        "data": pdf_bytes
                    }
                )
            ]
        )

        # Create a temporary session for this single request
        session = session_service.create_session(user_id="api_user", app_name="report_parser_app")
        print(f"Processing in temporary session: {session.id}")

        final_json_response = None
        # Asynchronously call the runner
        async for chunk in runner.run_async(
            user_id=session.user_id, session_id=session.id, new_message=message_with_pdf
        ):
            # The agent is designed to return the full JSON in the final response
            if chunk.is_final_response and chunk.content and chunk.content.parts:
                json_string = chunk.content.parts[0].text
                final_json_response = json.loads(json_string)
                break  # Exit after getting the final response

        if not final_json_response:
            raise HTTPException(status_code=500, detail="Agent failed to return a final JSON response.")

        print("✅ Extraction successful!")
        # FastAPI will automatically serialize this dict to a JSON response
        return final_json_response

    except Exception as e:
        print(f"❌ An error occurred: {e}")
        # Handle potential errors during agent processing
        raise HTTPException(status_code=500, detail=f"Failed to process the document: {str(e)}")


# --- 5. Root Endpoint for Health Check ---
@app.get("/")
def read_root():
    return {"status": "ok", "message": "Arogya Mitra Parser API is running."}

# --- 6. Make the App Runnable (for development) ---
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)