from google.adk.agents.llm_agent import Agent
from google.adk.tools.agent_tool import AgentTool




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
                { response: <Str>, duration: <int> ,aspect_ratio: <Str> }

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
- verifier_agent → writes 'verify_report' = { response: <Str>, duration: <int> ,aspect_ratio: <Str> }

SEQUENTIAL WORKFLOW (follow exactly; no alternative routes):
Step 1 (ALWAYS): Call director_agent to produce 'draft'.
Step 2 (ALWAYS): Call verifier_agent with the current 'draft'.


  - Copy the current 'draft' fields into 'final_response' as pure JSON:
    { "prompt": string, "duration_sec": int, "aspect_ratio": string }.


  """,
    sub_agents=[
        director_agent,
        verifier_agent,
    ]

)