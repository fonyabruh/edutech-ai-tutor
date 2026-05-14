import { useEffect } from "react";
import { Text, View } from "react-native";
import { router, useLocalSearchParams } from "expo-router";
import { MotiView } from "moti";
import { LoadingDots } from "@/components/ui";

const STEPS = [
  "Считаю твой уровень по темам…",
  "Сравниваю с требованиями экзамена…",
  "Готовлю персональные рекомендации…",
];

export default function AnalyzingScreen() {
  const { subject } = useLocalSearchParams<{ subject: string }>();

  useEffect(() => {
    const t = setTimeout(() => {
      router.replace(`/diagnostic/results?subject=${subject}`);
    }, 3800);
    return () => clearTimeout(t);
  }, [subject]);

  return (
    <View className="flex-1 bg-surface items-center justify-center px-8 gap-8">
      <View className="items-center gap-3">
        <Text className="text-2xl font-bold text-ink text-center">AI анализирует твои ответы</Text>
        <LoadingDots />
      </View>
      <View className="gap-4 w-full">
        {STEPS.map((step, i) => (
          <MotiView
            key={i}
            from={{ opacity: 0, translateX: -20 }}
            animate={{ opacity: 1, translateX: 0 }}
            transition={{ type: "timing", duration: 400, delay: 800 + i * 1000 }}
            className="flex-row items-center gap-3"
          >
            <MotiView
              from={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: "spring", delay: 800 + i * 1000 + 300 }}
            >
              <Text className="text-success text-xl">✓</Text>
            </MotiView>
            <Text className="text-ink text-base">{step}</Text>
          </MotiView>
        ))}
      </View>
    </View>
  );
}
