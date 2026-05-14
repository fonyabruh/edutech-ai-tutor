import { create } from "zustand";
import type { ChatMessage } from "@/lib/types";

interface ChatState {
  messages: Record<string, ChatMessage[]>;
  setMessages: (subjectCode: string, msgs: ChatMessage[]) => void;
  addMessage: (subjectCode: string, msg: ChatMessage) => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: {},
  setMessages: (subjectCode, msgs) =>
    set((s) => ({ messages: { ...s.messages, [subjectCode]: msgs } })),
  addMessage: (subjectCode, msg) =>
    set((s) => ({
      messages: {
        ...s.messages,
        [subjectCode]: [...(s.messages[subjectCode] ?? []), msg],
      },
    })),
}));
