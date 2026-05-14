import { useState } from "react";
import { Text, View } from "react-native";
import { router } from "expo-router";
import { Button, Chip, ProgressBar } from "@/components/ui";
import { useOnboardingStore } from "@/store/onboardingStore";

const GRADES = [8, 9, 10, 11];

export default function GradeStep() {
  const { grade, setGrade, setExam } = useOnboardingStore();
  const [selected, setSelected] = useState<number | null>(grade);

  const handleNext = () => {
    if (!selected) return;
    setGrade(selected);
    setExam(selected <= 9 ? "ОГЭ" : "ЕГЭ");
    router.push("/(onboarding)/exam");
  };

  return (
    <View className="flex-1 bg-surface px-6 py-10 justify-between">
      <View className="gap-6">
        <ProgressBar value={0.25} />
        <Text className="text-slate-400 text-sm">Шаг 1 из 4</Text>
        <Text className="text-2xl font-bold text-ink">В каком классе ты учишься?</Text>
        <View className="flex-row flex-wrap gap-3 mt-2">
          {GRADES.map((g) => (
            <Chip
              key={g}
              label={`${g} класс`}
              selected={selected === g}
              onPress={() => setSelected(g)}
              className="min-w-24 items-center"
            />
          ))}
        </View>
      </View>
      <Button label="Далее" onPress={handleNext} disabled={!selected} className="w-full" />
    </View>
  );
}
