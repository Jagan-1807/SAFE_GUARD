'use client';

import { useState, useRef, useEffect } from 'react';

interface ChatMessage {
  role: 'user' | 'bot';
  content: string;
  verified?: boolean;
  steps?: string[];
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function Home() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentSteps, setCurrentSteps] = useState<string[]>([]);
  const chatEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: ChatMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setCurrentSteps(['Connecting to Multi-Agent Backend...']);

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 60000);

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: input }),
        signal: controller.signal
      });

      clearTimeout(timeout);

      if (!response.ok) {
        const text = await response.text();
        throw new Error(`Backend Error: ${text}`);
      }

      const data = await response.json();

      if (!data.response) {
        throw new Error("Invalid response from backend");
      }

      const botMessage: ChatMessage = {
        role: 'bot',
        content: data.response,
        verified: data.verified,
        steps: data.steps || []
      };

      setMessages(prev => [...prev, botMessage]);
      setCurrentSteps(data.steps || []);

    } catch (error: any) {
      let errorMsg = "Something went wrong.";

      if (error.name === "AbortError") {
        errorMsg = "⏱ Request timed out. Backend not responding.";
      } else if (error.message.includes("Failed to fetch")) {
        errorMsg = "❌ Cannot connect to backend (check port 8000).";
      } else {
        errorMsg = error.message;
      }

      setMessages(prev => [
        ...prev,
        { role: 'bot', content: errorMsg }
      ]);

    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <header className="header">
        <div className="logo">SafeGuard AI</div>
        <div style={{ display: 'flex', gap: '1rem', color: '#94a3b8', fontSize: '0.9rem' }}>
          <span>Customer Support</span>
          <span>•</span>
          <span>Hallucination Verification Layer</span>
        </div>
      </header>

      <main className="main-app">
        <section className="chat-panel">
          <div className="chat-history">
            {messages.length === 0 && (
              <div style={{ textAlign: 'center', marginTop: '4rem', color: '#64748b' }}>
                <h2 style={{ color: 'white', marginBottom: '1rem' }}>
                  Ask anything about our policies
                </h2>
                <p>
                  Try: "What is your refund policy?" or "How long does shipping take?"
                </p>
              </div>
            )}

            {messages.map((m, i) => (
              <div key={i} className={`message ${m.role}`}>
                {m.content}

                {m.role === 'bot' && m.verified !== undefined && (
                  <div className={`verification-badge ${m.verified ? 'safe' : 'warning'}`}>
                    {m.verified
                      ? '✓ Strictly Grounded'
                      : '⚠ Hallucination Detected & Corrected'}
                  </div>
                )}
              </div>
            ))}

            {isLoading && (
              <div className="message bot">
                Thinking...
              </div>
            )}

            <div ref={chatEndRef} />
          </div>

          <div className="chat-input-area">
            <textarea
              rows={1}
              placeholder="Type your message here..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
            />
            <button className="send-btn" onClick={handleSend} disabled={isLoading}>
              {isLoading ? '...' : 'Send'}
            </button>
          </div>
        </section>

        <aside className="activity-panel">
          <div className="activity-title">
            <span
              className="dot"
              style={{ background: isLoading ? '#a855f7' : '#94a3b8' }}
            ></span>
            Agent Activity Log
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {currentSteps.length > 0 ? (
              currentSteps.map((step, i) => (
                <div
                  key={i}
                  className={`step-item ${
                    i === currentSteps.length - 1 && isLoading ? 'active' : ''
                  }`}
                >
                  <div className="dot"></div>
                  {step}
                </div>
              ))
            ) : (
              <div style={{ color: '#475569', fontSize: '0.85rem' }}>
                Waiting for query...
              </div>
            )}
          </div>

          <div
            style={{
              marginTop: 'auto',
              padding: '1rem',
              background: 'rgba(59, 130, 246, 0.05)',
              borderRadius: '12px',
              fontSize: '0.8rem',
              color: '#60a5fa',
              border: '1px solid rgba(59, 130, 246, 0.1)'
            }}
          >
            <strong>Multi-Agent Tip:</strong> Uses a Critic Agent to verify answers
            against retrieved documents before responding.
          </div>
        </aside>
      </main>
    </div>
  );
}