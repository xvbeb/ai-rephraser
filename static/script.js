const $ = id => document.getElementById(id);
const html = document.documentElement;
const input = $('inputText');
const toneSelect = $('toneSelect');
const resultContent = $('resultContent');
const chatMessages = $('chatMessages');
const chatInput = $('chatInput');
let busy = false;
let rewrittenText = '';

function setTheme(theme) {
  html.setAttribute('data-theme', theme);
  try { localStorage.setItem('theme', theme); } catch (_) { /* Storage may be disabled. */ }
  $('theme-toggle').textContent = theme === 'dark' ? '☀️' : '🌙';
}
let savedTheme;
try { savedTheme = localStorage.getItem('theme'); } catch (_) { /* Use system theme. */ }
setTheme(savedTheme || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'));
$('theme-toggle').addEventListener('click', () => setTheme(html.dataset.theme === 'dark' ? 'light' : 'dark'));

function setBusy(value) {
  busy = value;
  ['sendBtn', 'sendChatBtn', 'clearChatBtn', 'toneSelect'].forEach(id => { $(id).disabled = value; });
  $('copyBtn').disabled = value || !rewrittenText;
}

async function requestJSON(url, data) {
  const response = await fetch(url, data === undefined ? {} : {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data)
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || 'Ошибка сервера.');
  return result;
}

function showError(element, error) {
  element.classList.add('error');
  element.textContent = error instanceof TypeError ? 'Не удалось связаться с сервером.' : error.message;
}

function addMessage(role, content) {
  const div = document.createElement('div');
  div.classList.add('message', role === 'user' ? 'user' : 'assistant');
  div.textContent = content;
  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return div;
}

function renderHistory(history) {
  chatMessages.replaceChildren();
  history.forEach(message => addMessage(message.role, message.content));
}

async function loadChat() {
  const data = await requestJSON('/chat');
  renderHistory(data.history);
}

async function sendRequest() {
  if (busy) return;
  const text = input.value.trim();
  if (!text) { showError(resultContent, new Error('Введите текст!')); return; }
  setBusy(true);
  rewrittenText = '';
  resultContent.classList.remove('error');
  resultContent.textContent = '';
  resultContent.classList.add('loading');
  $('changesDetails').hidden = true;
  try {
    const data = await requestJSON('/rephrase', { text, tone: toneSelect.value });
    rewrittenText = data.rewritten_text;
    resultContent.textContent = rewrittenText;
    $('changesList').replaceChildren();
    data.changes.forEach(change => {
      const item = document.createElement('li');
      item.textContent = `${change.type}: ${change.description}`;
      $('changesList').appendChild(item);
    });
    $('changesDetails').hidden = data.changes.length === 0;
    // The new source replaces the previous refinement conversation.
    renderHistory([{ role: 'user', content: text }, { role: 'assistant', content: rewrittenText }]);
  } catch (error) {
    showError(resultContent, error);
  } finally {
    resultContent.classList.remove('loading');
    setBusy(false);
  }
}
$('sendBtn').addEventListener('click', sendRequest);
input.addEventListener('keydown', event => {
  if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') sendRequest();
});

$('copyBtn').addEventListener('click', async () => {
  if (!rewrittenText) return;
  try {
    try {
      await navigator.clipboard.writeText(rewrittenText);
    } catch (_) {
      // Embedded webviews may deny the async Clipboard API.
      const field = document.createElement('textarea');
      field.value = rewrittenText;
      field.style.position = 'fixed';
      field.style.opacity = '0';
      const focused = document.activeElement;
      document.body.appendChild(field);
      field.select();
      try {
        if (!document.execCommand('copy')) throw new Error('Clipboard unavailable');
      } finally {
        field.remove();
        focused?.focus();
      }
    }
    $('copyBtn').textContent = '✅';
  } catch (_) {
    $('copyBtn').textContent = '❌';
    $('copyBtn').title = 'Копирование недоступно. Выделите текст и скопируйте вручную.';
  }
  setTimeout(() => { $('copyBtn').textContent = '📋'; }, 1800);
});

async function readEvents(response, onEvent) {
  if (!response.ok) {
    const data = await response.json();
    throw new Error(data.error || 'Ошибка сервера.');
  }
  if (!response.body) throw new Error('Этот браузер не поддерживает потоковый ответ.');
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let doneReceived = false;
  try {
    while (true) {
      const { value, done } = await reader.read();
      buffer += decoder.decode(value, { stream: !done });
      let boundary;
      while ((boundary = buffer.indexOf('\n\n')) !== -1) {
        const frame = buffer.slice(0, boundary);
        buffer = buffer.slice(boundary + 2);
        const lines = frame.split('\n');
        const type = lines.find(line => line.startsWith('event: '))?.slice(7);
        const payload = lines.filter(line => line.startsWith('data: ')).map(line => line.slice(6)).join('\n');
        if (!payload) continue;
        // Parse complete SSE frames only; deltas contain plain text, not partial JSON.
        const data = JSON.parse(payload);
        if (type === 'error') throw new Error(data.error);
        onEvent(type, data);
        if (type === 'done') doneReceived = true;
      }
      if (done) break;
    }
    if (!doneReceived) throw new Error('Ответ прерван. Попробуйте отправить сообщение ещё раз.');
  } finally {
    await reader.cancel().catch(() => {});
    reader.releaseLock();
  }
}

async function sendChat() {
  if (busy) return;
  const message = chatInput.value.trim();
  if (!message) return;
  setBusy(true);
  addMessage('user', message);
  const answer = addMessage('assistant', '');
  answer.classList.add('loading');
  try {
    const response = await fetch('/chat/stream', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, tone: toneSelect.value })
    });
    await readEvents(response, (type, data) => {
      if (type === 'delta') {
        answer.classList.remove('loading');
        answer.textContent += data.text;
        chatMessages.scrollTop = chatMessages.scrollHeight;
      } else if (type === 'done') {
        renderHistory(data.history);
        if (chatInput.value.trim() === message) chatInput.value = '';
      }
    });
  } catch (error) {
    // Discard the incomplete preview; the server did not save it as an answer.
    showError(answer, error);
  } finally {
    answer.classList.remove('loading');
    setBusy(false);
  }
}
$('sendChatBtn').addEventListener('click', sendChat);
chatInput.addEventListener('keydown', event => {
  if (event.key === 'Enter' && !event.isComposing) sendChat();
});

$('clearChatBtn').addEventListener('click', async () => {
  if (busy || !confirm('Очистить весь чат? История будет потеряна.')) return;
  setBusy(true);
  try {
    await requestJSON('/chat/clear', {});
    renderHistory([]);
  } catch (error) {
    showError(addMessage('assistant', ''), error);
  } finally {
    setBusy(false);
  }
});

// Preserve the existing language selection control (UI preference only).
document.querySelectorAll('.lang-btn').forEach(button => {
  button.addEventListener('click', () => {
    document.querySelectorAll('.lang-btn').forEach(item => item.classList.remove('active'));
    button.classList.add('active');
    try { localStorage.setItem('lang', button.dataset.lang); } catch (_) { /* Optional. */ }
  });
});
window.addEventListener('load', () => {
  setTimeout(() => {
    $('loader')?.classList.add('hidden');
    setTimeout(() => $('loader')?.remove(), 800);
  }, 1200);
});
// Load once, avoiding polling races with an active generation.
setBusy(true);
loadChat().catch(error => showError(addMessage('assistant', ''), error)).finally(() => setBusy(false));
