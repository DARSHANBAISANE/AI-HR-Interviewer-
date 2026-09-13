lucide.createIcons();

let ws;
let currentAudio = null;
let recognition;
let isListening = false;
let finalTranscriptBuffer = '';
let sessionStartTime = null;
let timerInterval = null;

const BASE_API_URL = "http://127.0.0.1:8000";
const WS_URL = "ws://127.0.0.1:8000/ws/interview";

const visualizer = document.getElementById('audioVisualizer');
function startVisualizer() { if (visualizer) visualizer.classList.add('active'); }
function stopVisualizer() { if (visualizer) visualizer.classList.remove('active'); }

function startSessionTimer() {
    sessionStartTime = Date.now();
    const statusText = document.getElementById('statusText');
    
    timerInterval = setInterval(() => {
        const elapsed = Math.floor((Date.now() - sessionStartTime) / 1000);
        const minutes = String(Math.floor(elapsed / 60)).padStart(2, '0');
        const seconds = String(elapsed % 60).padStart(2, '0');
        if (statusText) statusText.innerText = `Live Session (${minutes}:${seconds})`;
    }, 1000);
}

function stopSessionTimer() {
    if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }
}

function handleFileSelect(event) {
    const file = event.target.files[0];
    const display = document.getElementById('fileNameDisplay');
    if (display) display.innerText = file ? `Selected: ${file.name}` : '';
}

async function handleFormSubmit(event) {
    event.preventDefault();

    const startBtn = document.getElementById('startBtn');
    startBtn.disabled = true;
    startBtn.innerHTML = `<span>Processing...</span>`;

    const name = document.getElementById('candidateName').value;
    const jd = document.getElementById('jobDesc').value;
    const pdfFile = document.getElementById('resumeFile').files[0];
    const textResume = document.getElementById('resumeText').value;

    const formData = new FormData();
    formData.append("candidate_name", name);
    formData.append("job_description", jd);
    formData.append("resume_text", textResume);
    if (pdfFile) {
        formData.append("resume_file", pdfFile);
    }

    try {
        const response = await fetch(`${BASE_API_URL}/api/upload-context`, {
            method: "POST",
            body: formData
        });

        const data = await response.json();
        if (data.status === "success") {
            startWebSocketSession(data);
        }
    } catch (err) {
        console.error("Upload error:", err);
        alert("Failed to connect to backend server at http://127.0.0.1:8000");
        startBtn.disabled = false;
        startBtn.innerHTML = `<span>Initialize Session</span><i data-lucide="arrow-right" size="18"></i>`;
        lucide.createIcons();
    }
}

function playBase64Audio(base64Audio) {
    if (!base64Audio) {
        stopVisualizer();
        return;
    }
    if (currentAudio) {
        currentAudio.pause();
        currentAudio = null;
    }
    currentAudio = new Audio("data:audio/mp3;base64," + base64Audio);
    
    startVisualizer();
    currentAudio.onended = () => {
        stopVisualizer();
    };
    currentAudio.play().catch(err => {
        console.error("Audio Playback Error:", err);
        stopVisualizer();
    });
}

function startWebSocketSession(contextData) {
    document.getElementById('setupPanel').style.display = 'none';
    document.getElementById('interviewPanel').style.display = 'block';

    updateStatus(true, "Connecting...");

    ws = new WebSocket(WS_URL);

    ws.onopen = () => {
        updateStatus(true, "Live Session");
        startSessionTimer();
        ws.send(JSON.stringify({
            candidate_name: contextData.candidate_name,
            resume_context: contextData.resume_context,
            job_description: contextData.job_description
        }));
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.interviewer_text) {
            appendMessage('Sarah (AI Lead)', data.interviewer_text, 'assistant');
        }
        if (data.audio_b64) {
            playBase64Audio(data.audio_b64);
        } else {
            stopVisualizer();
        }
    };

    ws.onerror = (err) => {
        console.error("WebSocket Error:", err);
        updateStatus(false, "Connection Error");
        stopSessionTimer();
        stopVisualizer();
    };

    ws.onclose = () => {
        updateStatus(false, "Session Ended");
        stopSessionTimer();
        stopVisualizer();
    };
}

function sendTextMessage() {
    const input = document.getElementById('userInput');
    const text = input.value.trim();
    if (!text || !ws || ws.readyState !== WebSocket.OPEN) return;

    appendMessage('You', text, 'user');
    ws.send(JSON.stringify({ user_text: text }));
    input.value = '';
    finalTranscriptBuffer = '';
    startVisualizer();
}

function toggleSpeechRecognition() {
    if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
        alert('Speech Recognition is not supported in this browser. Please use Chrome or Edge.');
        return;
    }

    const micBtn = document.getElementById('micBtn');

    if (!recognition) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';

        recognition.onresult = (event) => {
            let interimText = '';
            let finalText = '';

            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) {
                    finalText += event.results[i][0].transcript;
                } else {
                    interimText += event.results[i][0].transcript;
                }
            }

            if (finalText) {
                finalTranscriptBuffer += ' ' + finalText;
            }

            document.getElementById('userInput').value = (finalTranscriptBuffer + ' ' + interimText).trim();
        };

        recognition.onerror = (event) => {
            console.error("Speech recognition error", event.error);
            stopVisualizer();
        };

        recognition.onend = () => {
            isListening = false;
            micBtn.classList.remove('active');
            stopVisualizer();
            
            const inputVal = document.getElementById('userInput').value.trim();
            if (inputVal && ws && ws.readyState === WebSocket.OPEN) {
                sendTextMessage();
            }
        };
    }

    if (isListening) {
        recognition.stop();
        isListening = false;
        micBtn.classList.remove('active');
        stopVisualizer();
    } else {
        finalTranscriptBuffer = document.getElementById('userInput').value;
        recognition.start();
        isListening = true;
        micBtn.classList.add('active');
        startVisualizer();
    }
}

function handleKeyPress(e) {
    if (e.key === 'Enter') {
        if (isListening && recognition) {
            recognition.stop();
        }
        sendTextMessage();
    }
}

function appendMessage(sender, text, role) {
    const box = document.getElementById('chatBox');
    if (!box) return;
    
    const wrapper = document.createElement('div');
    wrapper.className = `msg-wrapper ${role}`;

    const author = document.createElement('div');
    author.className = 'msg-author';
    author.innerText = sender;

    const bubble = document.createElement('div');
    bubble.className = 'msg-bubble';
    bubble.innerText = text;

    wrapper.appendChild(author);
    wrapper.appendChild(bubble);
    box.appendChild(wrapper);

    box.scrollTop = box.scrollHeight;
}

function updateStatus(active, text) {
    const dot = document.getElementById('statusDot');
    const label = document.getElementById('statusText');
    
    if (label) label.innerText = text;
    if (dot) {
        if (active) {
            dot.classList.add('active');
        } else {
            dot.classList.remove('active');
        }
    }
}