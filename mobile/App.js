import { useEffect, useRef, useState } from "react";
import {
  FlatList,
  KeyboardAvoidingView,
  Platform,
  SafeAreaView,
  StatusBar,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { createSession, getHistory, getOrCreateUserId, sendMessage } from "./api";

// Scaffold proves the path works end-to-end against the same backend the web
// app uses — hardcoded to one city rather than porting the full city-switcher
// UI yet.
const CITY_ID = "ahmedabad";

export default function App() {
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState(null);
  const listRef = useRef(null);

  useEffect(() => {
    (async () => {
      try {
        const userId = await getOrCreateUserId();
        const id = await createSession(CITY_ID, userId);
        setSessionId(id);
        setMessages(await getHistory(id));
      } catch (e) {
        setError(e.message);
      }
    })();
  }, []);

  async function handleSend() {
    const text = input.trim();
    if (!text || sending || !sessionId) return;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setSending(true);
    try {
      const reply = await sendMessage(sessionId, text);
      setMessages((prev) => [...prev, { role: "assistant", content: reply }]);
    } catch (e) {
      setMessages((prev) => [...prev, { role: "assistant", content: `Error: ${e.message}` }]);
    } finally {
      setSending(false);
      requestAnimationFrame(() => listRef.current?.scrollToEnd({ animated: true }));
    }
  }

  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar barStyle="light-content" />
      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === "ios" ? "padding" : undefined}
      >
        <Text style={styles.header}>Local Buddy — Ahmedabad</Text>
        {error && <Text style={styles.error}>{error}</Text>}
        <FlatList
          ref={listRef}
          style={styles.flex}
          data={messages}
          keyExtractor={(_, i) => String(i)}
          contentContainerStyle={styles.messageList}
          onContentSizeChange={() => listRef.current?.scrollToEnd({ animated: true })}
          renderItem={({ item }) => (
            <View style={[styles.bubble, item.role === "user" ? styles.userBubble : styles.assistantBubble]}>
              <Text style={styles.bubbleText}>{item.content}</Text>
            </View>
          )}
        />
        {sending && <Text style={styles.thinking}>Thinking…</Text>}
        <View style={styles.inputRow}>
          <TextInput
            style={styles.input}
            value={input}
            onChangeText={setInput}
            placeholder="Ask about places to stay, food, customs, safety..."
            placeholderTextColor="#6b7280"
            onSubmitEditing={handleSend}
            editable={!sending}
          />
          <TouchableOpacity style={styles.sendButton} onPress={handleSend} disabled={sending}>
            <Text style={styles.sendButtonText}>Send</Text>
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: "#0f1115" },
  flex: { flex: 1 },
  header: { color: "#e6e6e6", fontSize: 18, fontWeight: "bold", padding: 16 },
  error: { color: "#ff8080", paddingHorizontal: 16, paddingBottom: 8 },
  messageList: { padding: 16, gap: 10 },
  bubble: { maxWidth: "80%", padding: 12, borderRadius: 12 },
  userBubble: { backgroundColor: "#2f6fed", alignSelf: "flex-end" },
  assistantBubble: { backgroundColor: "#1b1e26", borderWidth: 1, borderColor: "#2f333d", alignSelf: "flex-start" },
  bubbleText: { color: "#fff" },
  thinking: { color: "#9aa0aa", paddingHorizontal: 16, paddingBottom: 4 },
  inputRow: { flexDirection: "row", padding: 16, gap: 8, borderTopWidth: 1, borderTopColor: "#262a33" },
  input: { flex: 1, backgroundColor: "#1b1e26", color: "#e6e6e6", borderRadius: 8, paddingHorizontal: 12, paddingVertical: 10, borderWidth: 1, borderColor: "#2f333d" },
  sendButton: { backgroundColor: "#2f6fed", borderRadius: 8, paddingHorizontal: 18, justifyContent: "center" },
  sendButtonText: { color: "#fff", fontWeight: "600" },
});
