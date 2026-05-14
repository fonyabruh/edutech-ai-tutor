import { useEffect } from "react";
import { Text, View } from "react-native";
import Animated, { useAnimatedStyle, useSharedValue, withDelay, withTiming } from "react-native-reanimated";
import { Button } from "@/components/ui";
import type { LessonResult } from "@/lib/types";

interface SessionSummaryProps {
  summary: LessonResult;
  onHome: () => void;
  onMore: () => void;
}

export function SessionSummary({ summary, onHome, onMore }: SessionSummaryProps) {
  const { tasks_total, correct, mastery_before, mastery_after, xp_earned } = summary;
  const masteryVal = useSharedValue(mastery_before);

  useEffect(() => {
    masteryVal.value = withDelay(300, withTiming(mastery_after, { duration: 1500 }));
  }, [mastery_after]);

  const barStyle = useAnimatedStyle(() => ({
    width: `${masteryVal.value * 100}%`,
  }));

  const emoji = correct >= tasks_total / 2 ? "🎉" : "💪";

  return (
    <View className="flex-1 bg-surface items-center justify-center px-6 gap-6">
      <Text className="text-6xl">{emoji}</Text>
      <Text className="text-2xl font-bold text-ink text-center">
        {correct} из {tasks_total} правильно
      </Text>

      <View className="w-full gap-2">
        <View className="h-3 rounded-full bg-slate-200 overflow-hidden">
          <Animated.View className="h-full bg-primary rounded-full" style={barStyle} />
        </View>
        <View className="flex-row justify-between">
          <Text className="text-slate-400 text-xs">{Math.round(mastery_before * 100)}%</Text>
          <Text className="text-slate-400 text-xs">{Math.round(mastery_after * 100)}%</Text>
        </View>
      </View>

      <Text className="text-accent text-xl font-bold">+{xp_earned} XP</Text>
      <Text className="text-slate-500 text-base">Продолжай в том же духе! 🔥</Text>

      <View className="flex-row gap-3 w-full">
        <Button label="На главную" onPress={onHome} className="flex-1" />
        <Button label="Ещё одну тему" onPress={onMore} variant="ghost" className="flex-1" />
      </View>
    </View>
  );
}
