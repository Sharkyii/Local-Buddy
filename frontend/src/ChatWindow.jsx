import { useEffect, useRef, useState } from "react";
import { getHistory, sendMessage } from "./api.js";

export default function ChatWindow({ sessionId }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    setMessages([]);
    getHistory(sessionId).then(setMessages).catch(console.error);
  }, [sessionId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend() {
    const text = input.trim();
    if (!text || sending) return;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setSending(true);
    try {
      const reply = await sendMessage(sessionId, text);
      setMessages((prev) => [...prev, { role: "assistant", content: reply }]);
    } catch (error) {
      setMessages((prev) => [...prev, { role: "assistant", content: `Error: ${error.message}` }]);
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="chat-window">
      <div className="message-list">
        {messages.map((m, i) => (
          <div key={i} className={`message ${m.role}`}>
            {m.content}
          </div>
        ))}
        {sending && <div className="message assistant pending">Thinking…</div>}
        <div ref={bottomRef} />
      </div>
      <div className="input-row">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder="Ask about places to stay, food, customs, safety..."
          disabled={sending}
        />
        <button onClick={handleSend} disabled={sending}>
          Send
        </button>
      </div>
    </div>
  );
}
