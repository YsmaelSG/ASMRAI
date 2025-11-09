from google.adk.agents.llm_agent import Agent
from google.genai import types
from google.adk.tools.agent_tool import AgentTool

from typing import Optional, List, Dict, Any



ctx = {}
# session-scoped dictionary you pass between steps/agents
def save_memory(key: str, text: str) -> dict:
    ctx[key] = text          
    return {"stored_under": key}






# ----- SubAgent 1 -- The verifier

verifier_agent = Agent(
    model="gemini-2.5-flash",
    name="verifier_agent",
    description="tasked with ensuring every video has minimum requirements",
    instruction=("""
                 Your job is to solely make sure every text prompt includes the words:
                 High-Quality audio, atleast one ASMR trigger, soothing visuals, aesthetic background and calm and presentable.
                 4 <= duration_sec <= 8 and aspect_ratio ∈ {"16:9","9:16","1:1"}
                 "You verify the draft meets constraints. Respond ONLY as JSON with 'verify_report':"
                "{ 'ok': <bool>, 'issues': <list of strings> }

                 """),
    output_key="verify_report"


)

# ---- SubAgent 2 ---- The Director/Writer

director_agent = Agent(
    model="gemini-2.5-flash",
    name="director_agent",
    description="makes sure the videos are directed correctly",
    instruction=("""
                 ensure that detailed proper video angles and detailed cinematography is in place, being as descriptive as possible to please the User. 
                 Duration must be an integer between 4 and 8 inclusive; if user gives none, default to 5.
                 if no aspect_ratio given -> 16:9
                 Respond ONLY as JSON with key 'draft' containing:
                "{ 'prompt': <string>, 'duration_sec': <int>, 'aspect_ratio': <'16:9'|'9:16'|'1:1'> }.
                "Duration must be an integer. No extra text outside JSON."
                 """
                 ),
    output_key="draft"

)


#---- Subagent 3 ---- The evaluator/ aka bro fixes the code whenever the User doenst like it

evaluator_agent = Agent(
    model="gemini-2.5-flash",
    name="evaluator_agent",
    description="whenever the User doesnt like the video, ensures that you iterate each video",
    instruction="Whenever the User doenst like how the video is displayed, your job is to solely find the root cause and try to fix it.",
    output_key="evaluate_text"


)

# information in this format -> Video(BaseModel):response: str ,orderNumber: int



root_agent = Agent(
    model='gemini-2.5-flash',
    name='root_agent',
    
    description='Master agent tasked with creating the best prompt.',
    tools=[save_memory, AgentTool(agent=director_agent), AgentTool(agent=verifier_agent)],
    output_key="final_response",
    instruction="""
    Goal: Create an ASMR Veo 3.1 prompt that satisfies all constraints.

Available sub-agents (and their output keys):
- director_agent → writes 'draft' = { "prompt": string, "duration_sec": int, "aspect_ratio": "16:9"|"9:16"|"1:1" }
- verifier_agent → writes 'verify_report' = { "ok": bool, "issues": [string] }

SEQUENTIAL WORKFLOW (follow exactly; no alternative routes):
Step 1 (ALWAYS): Call director_agent to produce 'draft'.
Step 2 (ALWAYS): Call verifier_agent with the current 'draft'.

LOOP (repeat until verified or after 2 total verifier checks):
- If verify_report.ok == false:
    - Call director_agent again, using verify_report.issues to revise the draft.
    - Then call verifier_agent again.
- If verify_report.ok == true:
    - Proceed to Finalization.

PROHIBITION:
- Do NOT write 'final_response' at any time before verify_report.ok == true in the SAME turn.

FINALIZATION (copy-only):
- When and only when verify_report.ok == true in THIS turn:
  - Copy the current 'draft' fields into 'final_response' as pure JSON:
    { "prompt": string, "duration_sec": int, "aspect_ratio": string }.
- Otherwise, DO NOT produce 'final_response'. Continue the loop.

ITERATION LIMITS:
- You MUST perform Step 1 then Step 2 at least once before any attempt to finalize.
- You MUST NOT exceed 5 calls to director_agent or 4 calls to verifier_agent in total.


  """,
    sub_agents=[
        director_agent,
        verifier_agent,
    ]

)