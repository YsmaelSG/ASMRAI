import os, io, json, time, asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
from my_agent.agent import root_agent

load_dotenv()
api_curr_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_curr_key)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

APP_NAME = "agents"
SESSION_SERVICE = InMemorySessionService()
RUNNER = Runner(agent=root_agent, app_name=APP_NAME, session_service=SESSION_SERVICE)

GEN_SEM = asyncio.Semaphore(1)
RATE = {}
RATE_WINDOW = 60
RATE_MAX = 3
VIDEO_CACHE = {}
CACHE_TTL = 300

class Video(BaseModel):
    response: str

def add_asmr_to_text(txt: str) -> str:
    t = txt.strip()
    return f"{t} asmr" if "asmr" not in t.lower() else t

def rate_ok(user_id: str) -> bool:
    now = time.time()
    win = RATE.setdefault(user_id, [])
    while win and now - win[0] > RATE_WINDOW:
        win.pop(0)
    if len(win) >= RATE_MAX:
        return False
    win.append(now)
    return True

def cache_get(key: str):
    v = VIDEO_CACHE.get(key)
    if not v:
        return None
    data, ts = v
    if time.time() - ts > CACHE_TTL:
        VIDEO_CACHE.pop(key, None)
        return None
    return data

def cache_put(key: str, data: bytes):
    VIDEO_CACHE[key] = (data, time.time())

def _find_json_object(s: str):
    in_str = False
    esc = False
    depth = 0
    start = -1
    for i, ch in enumerate(s):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        else:
            if ch == '"':
                in_str = True
                continue
            if ch == '{':
                if depth == 0:
                    start = i
                depth += 1
            elif ch == '}':
                if depth > 0:
                    depth -= 1
                    if depth == 0 and start != -1:
                        return s[start:i+1]
    return None

def _json_try(x):
    if isinstance(x, dict):
        return x
    if isinstance(x, str):
        try:
            return json.loads(x)
        except Exception:
            frag = _find_json_object(x)
            if frag:
                try:
                    return json.loads(frag)
                except Exception:
                    return None
            return None
    return None

def _looks_like_plan(d):
    if not isinstance(d, dict):
        return False
    keys = {k.lower() for k in d.keys()}
    return {"prompt", "duration_sec", "aspect_ratio"}.issubset(keys)

def _extract_plan_from_state(state):
    if not isinstance(state, dict):
        return None
    paths = [
        ["final_response"],
        ["variables","final_response"],
        ["output","final_response"],
        ["data","final_response"],
        ["memory","final_response"],
        ["agent_outputs","final_response"],
    ]
    for path in paths:
        cur = state
        ok = True
        for k in path:
            if isinstance(cur, dict) and k in cur:
                cur = cur[k]
            else:
                ok = False
                break
        if ok:
            j = _json_try(cur)
            if _looks_like_plan(j):
                return j
    def walk(v):
        if isinstance(v, dict):
            if _looks_like_plan(v): return v
            for vv in v.values():
                r = walk(vv)
                if r: return r
        elif isinstance(v, list):
            for vv in v:
                r = walk(vv)
                if r: return r
        elif isinstance(v, str):
            j = _json_try(v)
            if _looks_like_plan(j): return j
        return None
    return walk(state)

def _extract_plan_from_events(events):
    for ev in reversed(list(events)):
        st = getattr(ev, "session_state", None)
        if st:
            j = _extract_plan_from_state(st)
            if _looks_like_plan(j):
                return j
        cnt = getattr(ev, "content", None)
        parts = getattr(cnt, "parts", None) if cnt else None
        if parts:
            for p in parts:
                t = getattr(p, "text", None)
                j = _json_try(t)
                if _looks_like_plan(j):
                    return j
                fc = getattr(p, "function_call", None)
                if fc:
                    args = getattr(fc, "args", None) or getattr(fc, "arguments", None)
                    j2 = _json_try(args)
                    if _looks_like_plan(j2):
                        return j2
    return None

async def _run_agent_get_plan(user_text: str):
    adk_user = "user1"
    session_id = "session1"
    try:
        await SESSION_SERVICE.create_session(app_name=APP_NAME, user_id=adk_user, session_id=session_id)
    except Exception:
        pass
    events = list(RUNNER.run(
        user_id=adk_user,
        session_id=session_id,
        new_message=Content(parts=[Part(text=user_text)]),
    ))
    try:
        session = await SESSION_SERVICE.get_session(app_name=APP_NAME, user_id=adk_user, session_id=session_id)
        state = getattr(session, "state", {}) or {}
    except Exception:
        state = {}
    plan = _extract_plan_from_state(state) or _extract_plan_from_events(events)
    if not _looks_like_plan(plan):
        plan = {"prompt": user_text, "duration_sec": 5, "aspect_ratio": "16:9"}
    return plan

async def _gen_video_with_retry(finalText: str):
    from google.genai.errors import ClientError
    attempt, delay = 0, 5
    while True:
        try:
            op = client.models.generate_videos(model="veo-3.1-generate-preview", prompt=str(finalText))
            while not op.done:
                await asyncio.sleep(2)
                op = client.operations.get(op)
                if op.error:
                    raise HTTPException(status_code=500, detail="video generation failed")
            return op.response.generatedVideos[0].video
        except ClientError as e:
            code = getattr(e, "status_code", None)
            if code == 429 and attempt < 3:
                await asyncio.sleep(delay)
                attempt += 1
                delay = min(delay * 2, 60)
                continue
            if code == 429:
                raise HTTPException(status_code=429, detail="Rate limit hit. Try again shortly.")
            raise

@app.post("/sendmoney")
async def getVideo(videoBody: Video):
    user_text = add_asmr_to_text(videoBody.response)
    user_id = "web"
    if not rate_ok(user_id):
        raise HTTPException(status_code=429, detail="Too many requests")

    cached = cache_get(user_text)
    if cached:
        async def chunker_c(bs: bytes, size: int = 524288):
            for i in range(0, len(bs), size):
                yield bs[i:i+size]
        return StreamingResponse(
            chunker_c(cached),
            media_type="video/mp4",
            headers={"Content-Disposition": 'inline; filename="generated.mp4"'},
        )

    plan = await _run_agent_get_plan(user_text)
    prompt = plan.get("prompt") or user_text
    try:
        duration_sec = int(plan.get("duration_sec", 5))
    except Exception:
        duration_sec = 5
    aspect_ratio = plan.get("aspect_ratio", "16:9")
    finalText = f"make the video {duration_sec} long and {aspect_ratio} long . Prompt: {prompt}"

    async with GEN_SEM:
        data = await _gen_video_with_retry(finalText)

    cache_put(user_text, data)

    async def chunker(bs: bytes, size: int = 524288):
        for i in range(0, len(bs), size):
            yield bs[i:i+size]

    return StreamingResponse(
        chunker(data),
        media_type="video/mp4",
        headers={"Content-Disposition": 'inline; filename=\"generated.mp4\"'},
    )
