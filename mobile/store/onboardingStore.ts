import { create } from "zustand";
import type { Exam, Goal } from "@/lib/types";

interface OnboardingState {
  grade: number | null;
  exam: Exam | null;
  subjects: string[];
  goal: Goal | null;
  setGrade: (grade: number) => void;
  setExam: (exam: Exam) => void;
  setSubjects: (subjects: string[]) => void;
  setGoal: (goal: Goal) => void;
  reset: () => void;
}

export const useOnboardingStore = create<OnboardingState>((set) => ({
  grade: null,
  exam: null,
  subjects: [],
  goal: null,
  setGrade: (grade) => set({ grade }),
  setExam: (exam) => set({ exam }),
  setSubjects: (subjects) => set({ subjects }),
  setGoal: (goal) => set({ goal }),
  reset: () => set({ grade: null, exam: null, subjects: [], goal: null }),
}));
