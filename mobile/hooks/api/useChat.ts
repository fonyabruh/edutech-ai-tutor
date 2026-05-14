import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { ChatMessage } from "@/lib/types";

export function useChatHistory(subjectCode: string) {
  return useQuery<ChatMessage[]>({
    queryKey: ["chat", subjectCode],
    queryFn: () =>
      api.get("/chat/history", { params: { subject_code: subjectCode } }).then((r) => r.data),
  });
}
