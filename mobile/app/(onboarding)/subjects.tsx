import { useState } from "react";
import { Text, View } from "react-native";
import { router } from "expo-router";
import { Button, Chip, ProgressBar } from "@/components/ui";
import { SUBJECTS } from "@/lib/subjects";
import { useOnboardingStore } from "@/store/onboardingStore";

export default function SubjectsStep() {
  const { subjects, setSubjects } = useOnboardingStore();
  const [selected, setSelected] = useState<string[]>(subjects);

  const toggle = (code: string) =>
    setSelected((prev) =>
      prev.includes(code) ? prev.filter((c) => c !== code) : [...prev, code]
    );

  const handleNext = () => {
    if (!selected.length) return;
    setSubjects(selected);
    router.push("/(onboarding)/goal");
  };

  return (
    <View className="flex-1 bg-surface px-6 py-10 justify-between">
      <View className="gap-6">
        <ProgressBar value={0.75} />
        <Text className="text-slate-400 text-sm">Шаг 3 из 4</Text>
        <Text className="text-2xl font-bold text-ink">Какие предметы готовишь?</Text>
        <Text className="text-slate-400">Можно выбрать несколько</Text>
        <View className="gap-3 mt-2">
          {SUBJECTS.map(({ code, label }) => (
            <Chip
              key={code}
              label={label}
              selected={selected.includes(code)}
              onPress={() => toggle(code)}
              className="w-full justify-center py-4"
            />
          ))}
        </View>
      </View>
      <Button label="Далее" onPress={handleNext} disabled={!selected.length} className="w-full" />
    </View>
  );
}
