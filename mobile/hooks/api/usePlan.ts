import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { LearningPlan } from "@/lib/types";

export function useCurrentPlan(subjectCode: string) {
  return useQuery<LearningPlan>({
    queryKey: ["plan", subjectCode],
    queryFn: () =>
      api.get("/plan/current", { params: { subject_code: subjectCode } }).then((r) => r.data),
    retry: false,
  });
}

export function useGeneratePlan() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (subject_code: string) =>
      api.post("/plan/generate", { subject_code }).then((r) => r.data),
    onSuccess: (_, subject_code) => {
      qc.invalidateQueries({ queryKey: ["plan", subject_code] });
    },
  });
}

export function useCompleteDay() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ dayIndex, subjectCode }: { dayIndex: number; subjectCode: string }) =>
      api
        .post(`/plan/day/${dayIndex}/complete`, null, { params: { subject_code: subjectCode } })
        .then((r) => r.data),
    onSuccess: (_, { subjectCode }) => {
      qc.invalidateQueries({ queryKey: ["plan", subjectCode] });
    },
  });
}
