import { useEffect, useRef, useState } from "react";
import { FlatList, KeyboardAvoidingView, Platform, Text, TextInput, TouchableOpacity, View } from "react-native";
import { useMySubjects } from "@/hooks/api/useMe";
import { useChatHistory } from "@/hooks/api/useChat";
import { useChatStore } from "@/store/chatStore";
import { useLLMStream } from "@/hooks/useLLMStream";
import { Card } from "@/components/ui";
import { LoadingDots } from "@/components/ui";

export default function ChatScreen() {
  const { data: subjects } = useMySubjects();
  const [activeCode, setActiveCode] = useState(subjects?.[0]?.code ?? "math_base");
  const { messages, setMessages, addMessage } = useChatStore();
  const { data: history } = useChatHistory(activeCode);
  const { text: streamText, isStreaming, start: startStream, reset } = useLLMStream();
  const [input, setInput] = useState("");
  const listRef = useRef<FlatList>(null);
  const idCounter = useRef(Date.now());

  useEffect(() => {
    if (history) setMessages(activeCode, history);
  }, [history, activeCode]);

  const send = () => {
    if (!input.trim()) return;
    const msg = input.trim();
    setInput("");
    reset();
    addMessage(activeCode, {
      id: idCounter.current++,
      role: "user",
      content: msg,
      created_at: new Date().toISOString(),
    });
    startStream("/chat/message", { subject_code: activeCode, message: msg });
  };

  const displayMessages = messages[activeCode] ?? [];

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === "ios" ? "padding" : undefined}
      keyboardVerticalOffset={Platform.OS === "ios" ? 90 : 0}
      className="flex-1 bg-surface"
    >
      <View className="px-6 pt-14 pb-3 flex-row gap-2">
        {(subjects ?? []).map((s) => (
          <TouchableOpacity
            key={s.code}
            onPress={() => setActiveCode(s.code)}
            className={`px-3 py-1.5 rounded-full ${activeCode === s.code ? "bg-primary" : "bg-slate-200"}`}
          >
            <Text className={`text-xs font-medium ${activeCode === s.code ? "text-white" : "text-ink"}`}>
              {s.name}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <FlatList
        ref={listRef}
        data={displayMessages}
        keyExtractor={(m) => String(m.id)}
        contentContainerStyle={{ padding: 16, gap: 8 }}
        onContentSizeChange={() => listRef.current?.scrollToEnd({ animated: true })}
        renderItem={({ item }) => (
          <View className={`max-w-5/6 ${item.role === "user" ? "self-end" : "self-start"}`}>
            <Card className={item.role === "user" ? "bg-primary" : "bg-white"}>
              <Text className={item.role === "user" ? "text-white" : "text-ink"}>{item.content}</Text>
            </Card>
          </View>
        )}
        ListFooterComponent={
          isStreaming ? (
            <Card className="self-start">
              {streamText ? <Text className="text-ink">{streamText}</Text> : <LoadingDots />}
            </Card>
          ) : null
        }
      />

      <View className="px-4 pb-8 pt-2 flex-row gap-2 items-end">
        <TextInput
          className="flex-1 bg-white border border-slate-200 rounded-2xl px-4 py-3 text-ink max-h-28"
          value={input}
          onChangeText={setInput}
          placeholder="Задай вопрос..."
          placeholderTextColor="#94a3b8"
          multiline
        />
        <TouchableOpacity
          onPress={send}
          disabled={!input.trim() || isStreaming}
          className="bg-primary rounded-2xl p-3 mb-0.5"
        >
          <Text className="text-white font-bold">→</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}
