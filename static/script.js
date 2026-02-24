// Тема
const html = document.documentElement;
const toggleBtn = document.getElementById('theme-toggle');

function setTheme(theme) {
  html.setAttribute('data-theme', theme);
  localStorage.setItem('theme', theme);
  toggleBtn.textContent = theme === 'dark' ? '☀️' : '🌙';
}

// Инициализация темы
let savedTheme = localStorage.getItem('theme') ||
  (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
setTheme(savedTheme);

toggleBtn.addEventListener('click', () => {
  const newTheme = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
  setTheme(newTheme);
});

// Основная логика переписывания
const input = document.getElementById('inputText');
const toneSelect = document.getElementById('toneSelect');
const sendBtn = document.getElementById('sendBtn');
const resultContent = document.getElementById('resultContent');
const copyBtn = document.getElementById('copyBtn');

async function sendRequest() {
  const text = input.value.trim();
  const tone = toneSelect.value;

  if (!text) {
    resultContent.innerHTML = '<span style="color: #ff6b6b;">Введите текст!</span>';
    return;
  }

  sendBtn.disabled = true;
  resultContent.innerHTML = '<span class="loading"></span>';
  resultContent.parentElement.classList.add('loading');

  try {
    const res = await fetch('/rephrase', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, tone })
    });

    const data = await res.json();

    if (data.error) {
      resultContent.innerHTML = `<span style="color: #ff6b6b;">Ошибка: ${data.error}</span>`;
    } else {
      resultContent.innerHTML = data.result.replace(/\n/g, '<br>');
    }
  } catch (err) {
    resultContent.innerHTML = `<span style="color: #ff6b6b;">Проблема: ${err.message}</span>`;
  } finally {
    sendBtn.disabled = false;
    resultContent.parentElement.classList.remove('loading');
  }
}

sendBtn.addEventListener('click', sendRequest);
input.addEventListener('keydown', e => {
  if (e.ctrlKey && e.key === 'Enter') sendRequest();
});

// Копирование результата
copyBtn.addEventListener('click', () => {
  const text = resultContent.innerText;
  navigator.clipboard.writeText(text).then(() => {
    copyBtn.textContent = '✅';
    setTimeout(() => copyBtn.textContent = '📋', 1800);
  });
});

// Чат
const chatMessages = document.getElementById('chatMessages');
const chatInput = document.getElementById('chatInput');
const sendChatBtn = document.getElementById('sendChatBtn');

let lastMessageCount = 0;
let wasAtBottom = true;

async function loadChat() {
  try {
    const res = await fetch('/chat');
    const data = await res.json();
    const history = data.history || [];

    if (history.length === lastMessageCount) return;

    const isAtBottomBefore = chatMessages.scrollHeight - chatMessages.scrollTop - chatMessages.clientHeight < 50;

    if (lastMessageCount === 0 || history.length < lastMessageCount) {
      chatMessages.innerHTML = '';
      lastMessageCount = 0;
    }

    for (let i = lastMessageCount; i < history.length; i++) {
      const msg = history[i];
      const div = document.createElement('div');
      div.classList.add('message', msg.role);
      div.textContent = msg.content;
      chatMessages.appendChild(div);
    }

    lastMessageCount = history.length;

    if (isAtBottomBefore || wasAtBottom) {
      chatMessages.scrollTop = chatMessages.scrollHeight;
      wasAtBottom = true;
    } else {
      wasAtBottom = false;
    }
  } catch (err) {
    console.error('Chat load error:', err);
  }
}

sendChatBtn.addEventListener('click', async () => {
  const text = chatInput.value.trim();
  if (!text) return;

  chatInput.value = '';  // очищаем поле сразу

  // Показываем индикатор загрузки в чате (не обязательно сообщение)
  chatMessages.insertAdjacentHTML('beforeend', 
    '<div class="message assistant loading">ИИ думает...</div>'
  );
  chatMessages.scrollTop = chatMessages.scrollHeight;

  try {
    const res = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text })
    });

    if (!res.ok) throw new Error('Ошибка сервера');

    // Удаляем индикатор "ИИ думает..."
    const loading = chatMessages.querySelector('.loading');
    if (loading) loading.remove();

    // Подгружаем свежую историю — там уже всё новое
    await loadChat();

  } catch (err) {
    // Показываем ошибку в чате
    const errorMsg = document.createElement('div');
    errorMsg.classList.add('message', 'assistant');
    errorMsg.style.color = '#ff6b6b';
    errorMsg.textContent = `Ошибка: ${err.message}`;
    chatMessages.appendChild(errorMsg);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }
});
// Переключатель языка (пока заглушка)
document.querySelectorAll('.lang-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.lang-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    localStorage.setItem('lang', btn.dataset.lang);
    console.log('Язык:', btn.dataset.lang);
  });
});

document.getElementById('clearChatBtn').addEventListener('click', async () => {
  if (!confirm('Очистить весь чат? История будет потеряна.')) return;

  try {
    // Отправляем запрос на сервер для очистки сессии
    await fetch('/chat/clear', { method: 'POST' });
    
    // Очищаем локально
    chatMessages.innerHTML = '';
    lastMessageCount = 0;
    wasAtBottom = true;
    
    // Можно показать системное сообщение
    const sysMsg = document.createElement('div');
    sysMsg.classList.add('message', 'assistant');
    sysMsg.textContent = 'Чат очищен. Начнём заново!';
    chatMessages.appendChild(sysMsg);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  } catch (err) {
    console.error('Ошибка очистки:', err);
  }
});

async function sendRequest() {
  const text = input.value.trim();
  const tone = toneSelect.value;

  if (!text) {
    resultContent.innerHTML = '<span style="color: #ff6b6b;">Введите текст!</span>';
    return;
  }

  sendBtn.disabled = true;
  resultContent.innerHTML = '<span class="loading"></span> Исправляю...';
  
  try {
    const res = await fetch('/rephrase', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, tone })
    });

    const data = await res.json();

    if (data.error) {
      resultContent.innerHTML = `<span style="color: #ff6b6b;">Ошибка: ${data.error}</span>`;
    } else {
      resultContent.innerHTML = data.result.replace(/\n/g, '<br>');
      
      // После исправления сразу подгружаем чат (там будет объяснение)
      await loadChat();
    }
  } catch (err) {
    resultContent.innerHTML = `<span style="color: #ff6b6b;">Проблема: ${err.message}</span>`;
  } finally {
    sendBtn.disabled = false;
  }
}

// Скрываем лоадер после полной загрузки страницы
window.addEventListener('load', () => {
  const loader = document.getElementById('loader');
  if (loader) {
    // Даём время на красивый fade-out (можно увеличить)
    setTimeout(() => {
      loader.classList.add('hidden');
      // Полностью удаляем через 1 сек после fade
      setTimeout(() => loader.remove(), 800);
    }, 1200); // 1.2 секунды — чтобы пользователь увидел анимацию
  }
});

// Polling чата
setInterval(loadChat, 4000);
loadChat(); // первый запуск