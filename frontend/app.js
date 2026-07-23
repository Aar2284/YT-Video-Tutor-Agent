const API_BASE = window.location.hostname === 'localhost'
    ? 'http://localhost:8000'
    : 'https://your-api-url.up.railway.app';

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

// Event Listeners
loadBtn.addEventListener('click', loadVideo);
askBtn.addEventListener('click', askQuestion);
questionInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !askBtn.disabled) askQuestion();
});
clearBtn.addEventListener('click', clearChat);

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
