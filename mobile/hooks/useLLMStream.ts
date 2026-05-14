import { useCallback, useState } from "react";
import { streamSSE } from "@/lib/sse";

export function useLLMStream() {
  const [text, setText] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);

  const start = useCallback((endpoint: string, body: object) => {
    setText("");
    setIsStreaming(true);
    streamSSE(
      endpoint,
      body,
      (chunk) => setText((prev) => prev + chunk),
      () => setIsStreaming(false),
      () => {
        setText((prev) => prev || "Связь нестабильна. Попробуй ещё раз.");
        setIsStreaming(false);
      }
    );
  }, []);

  const reset = useCallback(() => {
    setText("");
    setIsStreaming(false);
  }, []);

  return { text, isStreaming, start, reset };
}
