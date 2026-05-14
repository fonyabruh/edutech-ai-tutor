import { getToken } from "./storage";

const API_URL = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000";

export async function streamSSE(
  path: string,
  body: object,
  onChunk: (text: string) => void,
  onDone: () => void,
  onError?: (err: string) => void
): Promise<void> {
  const token = getToken();
  const response = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body),
  });

  if (!response.ok || !response.body) {
    onError?.(`HTTP ${response.status}`);
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      if (line.startsWith("event: chunk")) continue;
      if (line.startsWith("event: done")) {
        onDone();
        return;
      }
      if (line.startsWith("event: error")) continue;
      if (line.startsWith("data: ")) {
        try {
          const parsed = JSON.parse(line.slice(6));
          if (parsed.text) onChunk(parsed.text);
          if (parsed.error) onError?.(parsed.error);
        } catch {}
      }
    }
  }
  onDone();
}
