import os
import json
import base64
import tempfile
from io import BytesIO
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Form, UploadFile, File, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
from gtts import gTTS
from pypdf import PdfReader
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
import uvicorn

# ---------------------------------------------------------------------------
# 1. ENVIRONMENT & CONFIGURATION
# ---------------------------------------------------------------------------
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    raise ValueError(
        f"GROQ_API_KEY not found! Please verify that your .env file exists at '{env_path}' "
        "and contains GROQ_API_KEY=gsk_..."
    )

# Active Groq model identifier
PRIMARY_MODEL = "openai/gpt-oss-120b"

def text_to_audio_base64(text: str) -> str:
    try:
        tts = gTTS(text=text, lang="en", slow=False)
        fp = BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        return base64.b64encode(fp.read()).decode("utf-8")
    except Exception as e:
        print(f"gTTS Audio Generation Error: {e}")
        return ""

# ---------------------------------------------------------------------------
# 2. APPLICATION INITIALIZATION
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Single-Round Interactive HR AI Interviewer",
    description="Full setup platform with Job Description & PDF Resume uploaders.",
    version="1.4.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

groq_client = Groq(api_key=groq_api_key)

qdrant_client = QdrantClient(":memory:")
try:
    qdrant_client.create_collection(
        collection_name="hr_context",
        vectors_config=VectorParams(size=384, distance=Distance.COSINE)
    )
except Exception:
    pass

class ScorecardRequest(BaseModel):
    transcript: list

# ---------------------------------------------------------------------------
# 3. CONTEXT & FILE UPLOAD ENDPOINT (/api/upload-context)
# ---------------------------------------------------------------------------
@app.post("/api/upload-context")
async def upload_context(
    candidate_name: str = Form("Candidate"),
    job_description: str = Form(...),
    resume_text: str = Form(""),
    resume_file: UploadFile = File(None)
):
    extracted_resume = resume_text.strip()

    if resume_file:
        try:
            pdf_bytes = await resume_file.read()
            pdf_reader = PdfReader(BytesIO(pdf_bytes))
            extracted_pages = []
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    extracted_pages.append(text)
            
            pdf_text = "\n".join(extracted_pages).strip()
            if pdf_text:
                extracted_resume = f"{pdf_text}\n\n{extracted_resume}".strip()
        except Exception as e:
            print(f"PDF Extraction Error: {e}")

    if not extracted_resume:
        extracted_resume = "No resume details provided."

    return {
        "status": "success",
        "message": "Interview setup context processed successfully.",
        "candidate_name": candidate_name,
        "resume_context": extracted_resume,
        "job_description": job_description
    }

# ---------------------------------------------------------------------------
# 4. LIVE HR WEBSOCKET INTERVIEW ENDPOINT (/ws/interview)
# ---------------------------------------------------------------------------
@app.websocket("/ws/hr-interview")
@app.websocket("/ws/interview")
async def hr_interview_websocket(websocket: WebSocket):
    await websocket.accept()

    try:
        init_data = await websocket.receive_json()
    except Exception as e:
        print(f"Handshake error: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    candidate_name = init_data.get("candidate_name", "Candidate")
    resume_context = init_data.get("resume_context", "No resume provided.")
    job_description = init_data.get("job_description", "General role position.")

    session_history = [
        {
            "role": "system",
            "content": f"""
            You are Sarah, a Senior Talent Acquisition Lead conducting an initial HR screening interview with {candidate_name}.
            Tone: Warm, professional, encouraging, empathetic, yet evaluative.

            Candidate Resume Context:
            {resume_context}

            Job Description Context:
            {job_description}

            STRICT INTERVIEW RULE:
            - You MUST ask ONLY ONE question at a time.
            - Never ask multiple questions or bullet-pointed questions in a single turn.
            - Wait for the candidate's response before asking the next question.
            - Keep your responses concise (1 to 2 sentences max per turn) so the interview feels natural over voice.

            Interview Flow:
            1. Warmly introduce yourself and ask ONE initial question about their background or interest in the role.
            2. Based on their answer, acknowledge brief key points and ask ONE behavioral/experience question at a time using the STAR method.
            3. Ask ONE question regarding culture fit or workplace preferences.
            4. Ask ONE question regarding logistics (notice period / salary expectations).
            """
        }
    ]

    try:
        greeting_response = groq_client.chat.completions.create(
            model=PRIMARY_MODEL,
            messages=session_history,
            temperature=0.7
        )
        greeting_text = greeting_response.choices[0].message.content
        session_history.append({"role": "assistant", "content": greeting_text})
        
        greeting_audio_b64 = text_to_audio_base64(greeting_text)
        await websocket.send_json({
            "interviewer_text": greeting_text,
            "user_transcript": "",
            "audio_b64": greeting_audio_b64
        })
    except Exception as e:
        print(f"Greeting generation error: {e}")

    try:
        while True:
            message = await websocket.receive()
            user_text = ""

            if "bytes" in message:
                raw_audio = message["bytes"]
                with tempfile.NamedTemporaryFile(suffix=".webm", delete=True) as temp_audio:
                    temp_audio.write(raw_audio)
                    temp_audio.flush()
                    
                    with open(temp_audio.name, "rb") as file:
                        transcription = groq_client.audio.transcriptions.create(
                            file=(temp_audio.name, file.read()),
                            model="whisper-large-v3-turbo",
                            language="en"
                        )
                user_text = transcription.text

            elif "text" in message:
                data = json.loads(message["text"])
                user_text = data.get("user_text", "")

            if not user_text.strip():
                continue

            session_history.append({"role": "user", "content": user_text})

            response = groq_client.chat.completions.create(
                model=PRIMARY_MODEL,
                messages=session_history,
                temperature=0.7
            )
            interviewer_text = response.choices[0].message.content

            session_history.append({"role": "assistant", "content": interviewer_text})
            audio_b64 = text_to_audio_base64(interviewer_text)

            await websocket.send_json({
                "interviewer_text": interviewer_text,
                "user_transcript": user_text,
                "audio_b64": audio_b64
            })

    except WebSocketDisconnect:
        print(f"Session disconnected for {candidate_name}.")
    except Exception as e:
        print(f"Error in WebSocket session: {e}")
        try:
            await websocket.close()
        except RuntimeError:
            pass

# ---------------------------------------------------------------------------
# 5. HR EVALUATION SCORECARD GENERATOR (/api/hr/generate-scorecard)
# ---------------------------------------------------------------------------
@app.post("/api/hr/generate-scorecard")
async def generate_scorecard(payload: ScorecardRequest):
    if not payload.transcript:
        raise HTTPException(status_code=400, detail="Transcript cannot be empty.")

    eval_prompt = f"""
    Analyze the following transcript from an HR screening interview:
    {json.dumps(payload.transcript, indent=2)}

    Evaluate the candidate on a scale of 1-10 across these specific criteria:
    1. Communication & Verbal Clarity (1-10)
    2. STAR Method Execution (Behavioral Answers) (1-10)
    3. Culture & Team Alignment (1-10)
    4. Salary & Career Goal Alignment (1-10)

    Output a valid JSON object:
    {{
      "scores": {{
        "communication": 8,
        "star_execution": 7,
        "culture_fit": 9,
        "compensation_alignment": 8
      }},
      "overall_score": 8.0,
      "key_strengths": ["list of strengths"],
      "areas_for_improvement": ["list of areas"],
      "recommendation": "Hire / Follow-up / Pass",
      "hr_summary": "Concise summary."
    }}
    """

    try:
        response = groq_client.chat.completions.create(
            model=PRIMARY_MODEL,
            messages=[{"role": "user", "content": eval_prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scorecard generation error: {str(e)}")

# ---------------------------------------------------------------------------
# 6. SERVER EXECUTION BLOCK
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)