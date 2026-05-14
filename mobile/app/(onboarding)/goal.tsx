import { useState } from "react";
import { Text, View } from "react-native";
import { router } from "expo-router";
import { Button, Chip, ProgressBar } from "@/components/ui";
import { useOnboardingStore } from "@/store/onboardingStore";
import { useUpdateMe } from "@/hooks/api/useMe";
import type { Goal } from "@/lib/types";

const GOALS: { value: Goal; label: string }[] = [
  { value: "min", label: "Сдать на минимум" },
  { value: "good", label: "Получить хороший балл" },
  { value: "excellent", label: "Высокий балл (90+)" },
];

export default function GoalStep() {
  const { grade, exam, subjects, goal, setGoal } = useOnboardingStore();
  const [selected, setSelected] = useState<Goal | null>(goal);
  const updateMe = useUpdateMe();

  const handleDone = async () => {
    if (!selected) return;
    setGoal(selected);
    await updateMe.mutateAsync({
      grade: grade ?? undefined,
      exam: exam ?? undefined,
      goal: selected,
      subjects,
    });
    router.replace("/(tabs)/");
  };

  return (
    <View className="flex-1 bg-surface px-6 py-10 justify-between">
      <View className="gap-6">
        <ProgressBar value={1} />
        <Text className="text-slate-400 text-sm">Шаг 4 из 4</Text>
        <Text className="text-2xl font-bold text-ink">Какова твоя цель?</Text>
        <View className="gap-3 mt-2">
          {GOALS.map(({ value, label }) => (
            <Chip
              key={value}
              label={label}
              selected={selected === value}
              onPress={() => setSelected(value)}
              className="w-full justify-center py-4"
            />
          ))}
        </View>
      </View>
      <Button
        label="Готово"
        onPress={handleDone}
        disabled={!selected}
        loading={updateMe.isPending}
        className="w-full"
      />
    </View>
  );
}
