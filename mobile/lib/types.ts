export type Exam = "ОГЭ" | "ЕГЭ";
export type Goal = "min" | "good" | "excellent";
export type TaskType = "multi_choice" | "short_answer" | "numeric";

export interface User {
  id: string;
  grade: number | null;
  exam: Exam | null;
  goal: Goal | null;
  subjects: string;
  created_at: string;
  onboarding_completed: boolean;
  streak?: number;
}

export interface ProfilePatch {
  grade?: number;
  exam?: string;
  goal?: string;
  subjects?: string[];
}

export interface Subject {
  code: string;
  name: string;
  mastery_avg?: number;
  last_session_at?: string | null;
}

export interface Topic {
  id: number;
  name: string;
  codifier_code: string;
  exam_weight: number;
  mastery: number;
}

export interface Task {
  id: number;
  statement_md: string;
  type: TaskType;
  options: string[] | null;
  difficulty?: number;
}

export interface DiagnosticResult {
  id: number;
  subject_code: string;
  weak_topics: { topic_id: number; comment?: string }[];
  strong_topics: { topic_id: number; comment?: string }[];
  priority_skills: string[];
  estimated_score: number | null;
  llm_summary: string | null;
  created_at: string;
}

export interface PlanDay {
  day_index: number;
  topics: { topic_id: number; minutes: number; focus: string }[];
  summary: string;
  status?: "available" | "complete" | "locked";
}

export interface LearningPlan {
  id: number;
  subject_code: string;
  days: PlanDay[];
}

export interface LessonResult {
  tasks_total: number;
  correct: number;
  mastery_before: number;
  mastery_after: number;
  xp_earned: number;
}

export interface ChatMessage {
  id: number;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}
