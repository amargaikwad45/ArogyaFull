# report_parser_agent/agent.py

from google.adk.agents import Agent
from pydantic import BaseModel, Field

# --- 1. Define the exact JSON structure you want as output ---
# Using Pydantic models is the most reliable way to get structured data.

class Medication(BaseModel):
    """Describes a single medication."""
    name: str = Field(description="Name of the medication")
    dosage: str = Field(description="Dosage of the medication (e.g., '500mg')")

class PersonalInfo(BaseModel):
    """Describes the patient's personal details."""
    age: int = Field(description="The age of the patient as a number")
    sex: str = Field(description="The sex of the patient ('Male' or 'Female')")

class UserContext(BaseModel):
    """Contains all the extracted health information for the user."""
    user_name: str = Field(description="The full name of the patient")
    personal_info: PersonalInfo = Field(description="The patient's personal details like age and sex.")
    diagnosed_conditions: list[str] = Field(description="A list of all major diagnosed conditions or diseases")
    current_medications: list[Medication]

class ExpectedOutput(BaseModel):
    """The root JSON object that the agent must return."""
    user_context: UserContext
    interaction_history: list = Field(description="An empty list to initialize the conversation history.")

# --- 2. Create the Agent ---

report_parser_agent = Agent(
    name="report_parser_agent",
    # gemini-1.5-pro-latest is excellent for document analysis.
    model="gemini-2.5-flash",
    description="Parses PDF medical reports to extract structured user health context.",
    
    # This tells the agent it MUST return data matching the ExpectedOutput schema.
    output_schema=ExpectedOutput,

    instruction="""
    You are an expert medical data extraction bot. Your task is to analyze the provided document (a medical report)
    and extract the patient's information.
    
    You must call the provided tool to structure your response according to the schema.
    
    Fill in all the `user_context` fields based on the document.
    The `interaction_history` field MUST always be an empty list `[]`.
    
    If a specific piece of information (like a dosage) is not found, use a reasonable default
    like an empty string "" or null.
    """
)

# This line allows the ADK framework to find and run this agent.
root_agent = report_parser_agent
