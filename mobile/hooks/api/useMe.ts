import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { ProfilePatch, Subject, User } from "@/lib/types";

export function useMe() {
  return useQuery<User>({ queryKey: ["me"], queryFn: () => api.get("/me").then((r) => r.data) });
}

export function useUpdateMe() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (patch: ProfilePatch) => api.patch("/me", patch).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["me"] }),
  });
}

export function useMySubjects() {
  return useQuery<Subject[]>({
    queryKey: ["me", "subjects"],
    queryFn: () => api.get("/me/subjects").then((r) => r.data),
  });
}
