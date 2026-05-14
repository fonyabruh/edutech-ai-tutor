import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Topic } from "@/lib/types";

export function useTopics(subjectCode: string) {
  return useQuery<Topic[]>({
    queryKey: ["topics", subjectCode],
    queryFn: () => api.get(`/subjects/${subjectCode}/topics`).then((r) => r.data),
    enabled: !!subjectCode,
  });
}
