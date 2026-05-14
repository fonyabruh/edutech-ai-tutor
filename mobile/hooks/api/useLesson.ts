import { useMutation } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function useStartLesson() {
  return useMutation({
    mutationFn: (body: { subject_code: string; topic_id: number }) =>
      api.post("/lesson/start", body).then((r) => r.data),
  });
}

export function useAnswerLesson() {
  return useMutation({
    mutationFn: (body: { lesson_id: string; task_id: number; user_answer: string }) =>
      api.post("/lesson/answer", body).then((r) => r.data),
  });
}

export function useFinishLesson() {
  return useMutation({
    mutationFn: (lesson_id: string) =>
      api.post("/lesson/finish", { lesson_id }).then((r) => r.data),
  });
}
