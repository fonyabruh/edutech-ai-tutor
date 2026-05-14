export const SUBJECTS = [
  { code: "math_base", label: "Математика" },
  { code: "rus", label: "Русский язык" },
  { code: "soc", label: "Обществознание" },
] as const;

export const SUBJECT_NAME: Record<string, string> = Object.fromEntries(
  SUBJECTS.map((s) => [s.code, s.label])
);
