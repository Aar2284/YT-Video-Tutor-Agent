const API_BASE = '';

let sessionId = null;

// DOM Elements
const urlInput = document.getElementById('urlInput');
const loadBtn = document.getElementById('loadBtn');
const statusBar = document.getElementById('statusBar');
const transcriptInfo = document.getElementById('transcriptInfo');
const chatContainer = document.getElementById('chatContainer');
const emptyState = document.getElementById('emptyState');
const questionInput = document.getElementById('questionInput');
const askBtn = document.getElementById('askBtn');
const voiceToggle = document.getElementById('voiceToggle');
const clearBtn = document.getElementById('clearBtn');
const micBtn = document.getElementById('micBtn');

let mediaRecorder = null;
let audioChunks = [];

// Event Listeners
loadBtn.addEventListener('click', loadVideo);
askBtn.addEventListener('click', askQuestion);
questionInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !askBtn.disabled) askQuestion();
});
clearBtn.addEventListener('click', clearChat);
micBtn.addEventListener('click', toggleMic);

async function loadVideo() {
    const url = urlInput.value.trim();
    if (!url) return;

    setStatus('loading', 'Loading video transcript...');
    loadBtn.disabled = true;

    try {
        const res = await fetch(`${API_BASE}/api/load-video`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url }),
        });

        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.detail || 'Failed to load video');
        }

        sessionId = data.session_id;
        setStatus('success', data.message);
        transcriptInfo.style.display = 'block';
        transcriptInfo.textContent = `Language: ${data.language} | Segments: ${data.segment_count}`;
        questionInput.disabled = false;
        askBtn.disabled = false;
        micBtn.disabled = false;
        clearBtn.disabled = false;
        emptyState.textContent = 'Video loaded! Ask a question about the content.';
    } catch (err) {
        setStatus('error', err.message);
    } finally {
        loadBtn.disabled = false;
    }
}

async function askQuestion() {
    const question = questionInput.value.trim();
    if (!question || !sessionId) return;

    addMessage('user', question);
    questionInput.value = '';
    questionInput.disabled = true;
    askBtn.disabled = true;

    const typingEl = addTypingIndicator();

    try {
        const res = await fetch(`${API_BASE}/api/ask`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: sessionId,
                question,
                use_voice: voiceToggle.checked,
            }),
        });

        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.detail || 'Failed to get answer');
        }

        typingEl.remove();
        addMessage('assistant', data.answer, data.sources, data.audio_url);
    } catch (err) {
        typingEl.remove();
        addMessage('assistant', `Error: ${err.message}`);
    } finally {
        questionInput.disabled = false;
        askBtn.disabled = false;
        questionInput.focus();
    }
}

function addMessage(role, content, sources = null, audioUrl = null) {
    emptyState.style.display = 'none';

    const msg = document.createElement('div');
    msg.className = `message ${role}`;

    const iconLabel = role === 'user' ? 'U' : 'AI';
    const iconClass = role === 'user' ? 'user' : 'assistant';

    let sourcesHtml = '';
    if (sources && sources.length > 0) {
        sourcesHtml = `<div class="message-sources">Sources: ${sources.join(', ')}</div>`;
    }

    let audioHtml = '';
    if (audioUrl) {
        audioHtml = `
            <div class="message-audio">
                <audio controls src="${API_BASE}${audioUrl}"></audio>
            </div>
        `;
    }

    msg.innerHTML = `
        <div class="message-header">
            <span class="icon ${iconClass}">${iconLabel}</span>
            <span>${role === 'user' ? 'You' : 'Tutor'}</span>
        </div>
        <div class="message-body">${escapeHtml(content)}</div>
        ${sourcesHtml}
        ${audioHtml}
    `;

    chatContainer.appendChild(msg);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function addTypingIndicator() {
    const msg = document.createElement('div');
    msg.className = 'message assistant';
    msg.innerHTML = `
        <div class="message-header">
            <span class="icon assistant">AI</span>
            <span>Tutor</span>
        </div>
        <div class="message-body typing-indicator">
            <span></span><span></span><span></span>
        </div>
    `;
    chatContainer.appendChild(msg);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    return msg;
}

function clearChat() {
    chatContainer.innerHTML = '';
    chatContainer.appendChild(emptyState);
    emptyState.style.display = 'block';
    emptyState.textContent = 'Video loaded! Ask a question about the content.';

    if (sessionId) {
        fetch(`${API_BASE}/api/session/${sessionId}`, { method: 'DELETE' });
    }
    sessionId = null;
    urlInput.value = '';
    questionInput.disabled = true;
    askBtn.disabled = true;
    micBtn.disabled = true;
    clearBtn.disabled = true;
    transcriptInfo.style.display = 'none';
    statusBar.style.display = 'none';
}

function setStatus(type, message) {
    statusBar.className = `status ${type}`;
    statusBar.textContent = message;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

async function toggleMic() {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
        micBtn.classList.remove('recording');
        return;
    }

    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
        const source = audioCtx.createMediaStreamSource(stream);
        const processor = audioCtx.createScriptProcessor(4096, 1, 1);

        let pcmData = [];
        processor.onaudioprocess = (e) => {
            const input = e.inputBuffer.getChannelData(0);
            pcmData.push(new Float32Array(input));
        };

        source.connect(processor);
        processor.connect(audioCtx.destination);

        mediaRecorder = { state: 'recording' };
        micBtn.classList.add('recording');
        addMessage('user', 'Recording... speak now');

        const startTime = Date.now();
        const stopRecording = () => {
            processor.disconnect();
            source.disconnect();
            audioCtx.close();
            stream.getTracks().forEach(t => t.stop());
            micBtn.classList.remove('recording');
            mediaRecorder = null;

            const wavBlob = encodeWAV(pcmData, 16000);
            const reader = new FileReader();
            reader.onloadend = async () => {
                const b64 = reader.result.split(',')[1];
                const typingEl = addTypingIndicator();
                try {
                    const res = await fetch(`${API_BASE}/api/stt`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            session_id: sessionId,
                            audio_base64: b64,
                            language: 'en',
                        }),
                    });
                    const data = await res.json();
                    typingEl.remove();
                    if (data.text && data.text.trim()) {
                        questionInput.value = data.text;
                        addMessage('user', `[Voice] ${data.text}`);
                    } else {
                        addMessage('assistant', 'Could not understand the audio. Please try again.');
                    }
                } catch (err) {
                    typingEl.remove();
                    addMessage('assistant', `STT failed: ${err.message}`);
                }
            };
            reader.readAsDataURL(wavBlob);
        };

        mediaRecorder.stop = stopRecording;

        setTimeout(() => {
            if (mediaRecorder && mediaRecorder.state === 'recording') {
                stopRecording();
            }
        }, 30000);
    } catch (err) {
        addMessage('assistant', 'Microphone access denied. Please allow microphone access and try again.');
    }
}

function encodeWAV(channels, sampleRate) {
    let length = 0;
    for (const ch of channels) length += ch.length;
    const buffer = new ArrayBuffer(44 + length * 2);
    const view = new DataView(buffer);

    const writeStr = (offset, str) => {
        for (let i = 0; i < str.length; i++) view.setUint8(offset + i, str.charCodeAt(i));
    };

    writeStr(0, 'RIFF');
    view.setUint32(4, 36 + length * 2, true);
    writeStr(8, 'WAVE');
    writeStr(12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, 1, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * 2, true);
    view.setUint16(32, 2, true);
    view.setUint16(34, 16, true);
    writeStr(36, 'data');
    view.setUint32(40, length * 2, true);

    let offset = 44;
    for (const ch of channels) {
        for (let i = 0; i < ch.length; i++) {
            let s = Math.max(-1, Math.min(1, ch[i]));
            view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
            offset += 2;
        }
    }

    return new Blob([buffer], { type: 'audio/wav' });
}
