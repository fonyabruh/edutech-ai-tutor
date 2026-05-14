import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { DiagnosticResult } from "@/lib/types";

export function useDiagnosticResult(subjectCode: string) {
  return useQuery<DiagnosticResult>({
    queryKey: ["diagnostic", subjectCode],
    queryFn: () => api.get(`/diagnostic/result/${subjectCode}`).then((r) => r.data),
    retry: false,
  });
}

export function useStartDiagnostic() {
  return useMutation({
    mutationFn: (subject_code: string) =>
      api.post("/diagnostic/start", { subject_code }).then((r) => r.data),
  });
}

export function useAnswerDiagnostic() {
  return useMutation({
    mutationFn: (body: { session_id: string; task_id: number; user_answer: string | null }) =>
      api.post("/diagnostic/answer", body).then((r) => r.data),
  });
}

export function useFinishDiagnostic() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { session_id: string; subject_code: string }) =>
      api.post("/diagnostic/finish", body).then((r) => r.data),
    onSuccess: (_, vars) => {
      qc.invalidateQueries({ queryKey: ["diagnostic", vars.subject_code] });
    },
  });
}
