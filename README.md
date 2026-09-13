# ⚡ Voice RAG HR Interviewer

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Vector DB](https://img.shields.io/badge/Vector_DB-Qdrant-red.svg)](https://qdrant.tech/)
[![Frontend](https://img.shields.io/badge/Frontend-HTML%2FJS-blueviolet.svg)](https://developer.mozilla.org/)
[![LLM Engine](https://img.shields.io/badge/AI_Engine-Groq_Whisper_%26_Llama-orange.svg)](https://groq.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A production-oriented real-time voice-enabled HR screening interview platform designed for dynamic candidate evaluation.
Unlike traditional text-only chat applications, this project combines real-time WebSocket audio streaming, Speech-to-Text transcription via Whisper, Retrieval-Augmented Generation (RAG) using Qdrant, and high-speed LLM inference through Groq to conduct automated screening interviews.
The system supports PDF resume ingestion, live voice/text interaction, source-grounded conversation, and automated evaluation scorecards.



## 🚀 Technologies Used

### 💻 Backend & Application
* **Python**
* **FastAPI** — REST API backend & WebSocket handler
* **Uvicorn** — ASGI server

### 🎙️ Speech & NLP
* **Groq API** — High-speed LLM inference
* **Whisper (`whisper-large-v3-turbo`)** — Real-time speech-to-text transcription
* **gTTS (Google Text-to-Speech)** — Natural voice response generation

### 📄 Document Processing & Data
* **PyPDF** — PDF resume text extraction
* **Qdrant** — In-memory vector database for context management

### 🎨 Frontend
* **HTML5, Vanilla JavaScript, CSS3** — Interactive web interface

---

## 🔍 How the System Works

### 1. 📄 Context & File Ingestion
The system accepts candidate names, job descriptions, and resumes (uploaded as text or PDF files). PDF files are processed using PyPDF to extract candidate details for the interview session.
Candidate Input / Resume Upload
              ↓
    Text Extraction (PyPDF)
              ↓
     Session Initialization

### 2. ⚡ Real-Time WebSocket Connection
Once context is initialized, a WebSocket connection opens between the frontend client and the FastAPI backend to handle real-time conversational streaming.
Frontend Client
       ↓
WebSocket Handshake (`/ws/hr-interview`)
       ↓
Dynamic System Prompt Generation (Sarah, Senior Talent Acquisition Lead)

### 3. 🎙️ Voice Input & Transcription
Candidates can respond using voice audio. The raw audio stream is temporarily recorded, processed, and transcribed into text using Whisper via the Groq API.
Audio Stream (WebM)
       ↓
Temporary File Buffer
       ↓
Groq Whisper (`whisper-large-v3-turbo`)
       ↓
Candidate Transcript

### 4. 🤖 AI Interviewer Evaluation & Response
The transcript is appended to the conversation history and evaluated by the primary model using strict prompt constraints (asking one question at a time, keeping responses concise, and utilizing the STAR method).
User Transcript
      +
Session History
      ↓
Groq LLM Inference
      ↓
Interviewer Response Text

### 5. 🔊 Text-to-Speech Synthesis
The generated interviewer text is converted into an audio stream using gTTS, encoded in Base64, and sent back through the WebSocket alongside the text.
Interviewer Text
      ↓
Google Text-to-Speech (`gTTS`)
      ↓
Base64 Audio Encoding
      ↓
Sent to Client Interface

### 6. 📊 Automated Evaluation Scorecard
At the end of the interview, the complete transcript is analyzed to generate a structured JSON evaluation scorecard assessing communication, STAR execution, culture fit, and compensation alignment.
Interview Transcript
      ↓
Scorecard Evaluation Prompt
      ↓
Groq LLM (JSON Mode)
      ↓
Structured Candidate Scorecard

---

## 🏗️ System Architecture

                         ┌──────────────────────────┐
                         │       Frontend UI        │
                         │    HTML / CSS / JS       │
                         └────────────┬─────────────┘
                                      │
                                      │ WebSockets & REST API
                                      ▼
                         ┌──────────────────────────┐
                         │      FastAPI Backend     │
                         └────────────┬─────────────┘
                                      │
                         ┌────────────┴────────────┐
                         │                         │
                         ▼                         ▼
               ┌──────────────────┐      ┌──────────────────┐
               │ Context Ingestion│      │ Real-Time WS     │
               │ Pipeline         │      │ Interview Loop   │
               ├──────────────────┤      ├──────────────────┤
               │ PDF Extraction   │      │ Whisper STT      │
               │ Qdrant Vector DB │      │ Groq LLM Engine  │
               └────────┬─────────│      │ gTTS Audio Gen   │
                        │         └──────┴────────┬─────────┘
                        │                         │
                        └────────────┬────────────┘
                                     ▼
                           ┌──────────────────┐
                           │   Automated HR   │
                           │    Scorecard     │
                           └──────────────────┘

---

## ✨ Key Features

* **Real-Time Voice Streaming**: Bi-directional audio and text exchange over WebSockets for a natural interview flow.
* **Single-Question Constraint**: System prompts enforce strict interviewer discipline to ask only one question at a time.
* **Automated Speech Pipeline**: Integrated Whisper STT and gTTS audio synthesis.
* **Structured Evaluation**: Generates quantitative scores (1-10) and qualitative feedback across core hiring metrics.
* **Robust File Handling**: Seamlessly extracts text from uploaded PDF resumes.

---

## 🧠 Concepts Practiced

* Real-Time WebSockets
* FastAPI Backend Development
* Speech-to-Text & Text-to-Speech Integration
* LLM Prompt Engineering & Constraints
* Structured JSON Output Generation
* Audio Stream Processing

---

## 🎯 Project Goal

The goal of the AI HR Interviewer Platform was to explore conversational voice agents built on top of modern LLMs and audio pipelines. Moving beyond static text chat, the system simulates a realistic, empathetic, and structured recruitment screening call complete with automated performance scoring.

---

## 🔮 Future Improvements

Potential future enhancements include:
* Persistent database storage for candidate history
* Advanced speech models for hyper-realistic voice cloning
* Multi-round interview workflows (Technical & System Design rounds)
* Recruiter dashboard for analytics and candidate management
* WebRTC integration for lower-latency audio streaming
* Docker-based deployment

---

## 👨‍💻 Author

**Darshan Baisane**

AI Engineer | Generative AI | LLMs | RAG | AI Agents

---

## 🔗 Connect

* **GitHub**: [https://github.com/DARSHANBAISANE](https://github.com/DARSHANBAISANE)
* **LinkedIn**: [https://www.linkedin.com/in/darshan-baisane-313566265/](https://www.linkedin.com/in/darshan-baisane-313566265/)

---

## ⭐ Support

If you find this project useful or interesting, consider giving the repository a ⭐ on GitHub.
