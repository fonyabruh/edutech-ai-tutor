import { useState } from "react";
import { Text, View } from "react-native";
import { router } from "expo-router";
import { Button, Chip, ProgressBar } from "@/components/ui";
import { useOnboardingStore } from "@/store/onboardingStore";
import type { Exam } from "@/lib/types";

const EXAMS: { value: Exam; label: string; desc: string }[] = [
  { value: "ОГЭ", label: "ОГЭ", desc: "9 класс" },
  { value: "ЕГЭ", label: "ЕГЭ", desc: "11 класс" },
];

export default function ExamStep() {
  const { exam, setExam } = useOnboardingStore();
  const [selected, setSelected] = useState<Exam | null>(exam);

  const handleNext = () => {
    if (!selected) return;
    setExam(selected);
    router.push("/(onboarding)/subjects");
  };

  return (
    <View className="flex-1 bg-surface px-6 py-10 justify-between">
      <View className="gap-6">
        <ProgressBar value={0.5} />
        <Text className="text-slate-400 text-sm">Шаг 2 из 4</Text>
        <Text className="text-2xl font-bold text-ink">Какой экзамен сдаёшь?</Text>
        <View className="gap-3 mt-2">
          {EXAMS.map(({ value, label, desc }) => (
            <Chip
              key={value}
              label={`${label} — ${desc}`}
              selected={selected === value}
              onPress={() => setSelected(value)}
              className="w-full justify-center py-4"
            />
          ))}
        </View>
      </View>
      <Button label="Далее" onPress={handleNext} disabled={!selected} className="w-full" />
    </View>
  );
}
