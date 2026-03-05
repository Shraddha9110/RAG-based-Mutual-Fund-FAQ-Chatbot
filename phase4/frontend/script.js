document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const lastUpdatedTime = document.getElementById('last-updated-time');
    const fundCount = document.getElementById('fund-count');

    const API_URL = 'http://localhost:8000/chat';
    const LAST_UPDATED_URL = 'http://localhost:8000/last-updated';
    const SUGGESTIONS_URL = 'http://localhost:8000/suggestions';

    // Fetch and display last updated time
    async function fetchLastUpdated() {
        try {
            const response = await fetch(LAST_UPDATED_URL);
            if (response.ok) {
                const data = await response.json();

                if (data.last_updated) {
                    const date = new Date(data.last_updated);
                    lastUpdatedTime.textContent = date.toLocaleString();
                } else {
                    lastUpdatedTime.textContent = 'Not available';
                }

                fundCount.textContent = data.total_funds || '-';
            } else {
                lastUpdatedTime.textContent = 'Error loading';
                fundCount.textContent = '-';
            }
        } catch (error) {
            console.error('Error fetching last updated:', error);
            lastUpdatedTime.textContent = 'Offline';
            fundCount.textContent = '-';
        }
    }

    // Load last updated info on page load
    fetchLastUpdated();

    // Refresh last updated info every 60 seconds
    setInterval(fetchLastUpdated, 60000);

    // Fetch and display dynamic suggestions
    async function fetchSuggestions() {
        const suggestionContainer = document.getElementById('suggestion-container');
        try {
            const response = await fetch(SUGGESTIONS_URL);
            if (response.ok) {
                const data = await response.json();
                suggestionContainer.innerHTML = '';

                if (data.suggestions && data.suggestions.length > 0) {
                    data.suggestions.forEach(question => {
                        const item = document.createElement('div');
                        item.classList.add('sugg-item');

                        const text = document.createElement('span');
                        text.classList.add('sugg-name');
                        text.textContent = question;

                        const btn = document.createElement('button');
                        btn.classList.add('add-btn');
                        btn.textContent = "Ask";

                        item.appendChild(text);
                        item.appendChild(btn);

                        // Handle clicking to ask
                        item.addEventListener('click', () => {
                            userInput.value = question;
                            handleSend();
                        });

                        suggestionContainer.appendChild(item);
                    });
                } else {
                    suggestionContainer.innerHTML = '<div style="font-size: 13px; color: var(--text-muted); padding: 10px;">No suggestions available.</div>';
                }
            }
        } catch (error) {
            console.error('Error fetching suggestions:', error);
            suggestionContainer.innerHTML = '<div style="font-size: 13px; color: var(--text-muted); padding: 10px;">Could not load suggestions.</div>';
        }
    }

    // Load suggestions on page load
    fetchSuggestions();

    function addMessage(text, sender, source = null) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', sender);

        const img = document.createElement('img');
        if (sender === 'bot') {
            img.src = 'https://ui-avatars.com/api/?name=MF+Bot&background=FFB300&color=fff';
        } else {
            img.src = 'https://ui-avatars.com/api/?name=User&background=5D87FF&color=fff';
        }
        img.alt = sender;

        const bubble = document.createElement('div');
        bubble.classList.add('message-bubble');

        // Format link if source exists
        let content = text;
        if (source && source !== "None" && !text.includes(source)) {
            content += `<br><br><strong>Source:</strong> <a href="${source}" target="_blank" style="color: inherit; text-decoration: underline;">${source}</a>`;
        }

        bubble.innerHTML = content;

        const timeSpan = document.createElement('span');
        timeSpan.classList.add('msg-time');
        const now = new Date();
        timeSpan.textContent = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;

        bubble.appendChild(timeSpan);
        messageDiv.appendChild(img);
        messageDiv.appendChild(bubble);

        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    async function handleSend() {
        const query = userInput.value.trim();
        if (!query) return;

        // Add user message
        addMessage(query, 'user');
        userInput.value = '';
        userInput.focus(); // Keep focus on input for next question

        // Add loading indicator (optional but better UX)
        const loadingId = 'loading-' + Date.now();
        const loadingDiv = document.createElement('div');
        loadingDiv.id = loadingId;
        loadingDiv.classList.add('message', 'bot');
        loadingDiv.style.opacity = '0.5';
        loadingDiv.innerHTML = `<img src="https://ui-avatars.com/api/?name=MF+Bot&background=FFB300&color=fff" alt="bot">
                                <div class="message-bubble">Thinking...</div>`;
        chatMessages.appendChild(loadingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        try {
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query: query }),
            });

            const data = await response.json();

            // Remove loading indicator
            document.getElementById(loadingId).remove();

            if (response.ok) {
                addMessage(data.answer, 'bot', data.source);
            } else {
                addMessage("Sorry, I encountered an error: " + (data.detail || "Unknown error"), 'bot');
            }
        } catch (error) {
            document.getElementById(loadingId).remove();
            addMessage("Could not connect to the backend. Please ensure the FastAPI server is running.", 'bot');
            console.error("Fetch error:", error);
        }
    }

    sendBtn.addEventListener('click', handleSend);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleSend();
        }
    });
});
