import { FlatList, Text, View } from "react-native";
import { router, useLocalSearchParams } from "expo-router";
import { MotiView } from "moti";
import { Button, Card } from "@/components/ui";
import { useCurrentPlan } from "@/hooks/api/usePlan";
import type { PlanDay } from "@/lib/types";

function DayCard({
  day,
  index,
  isToday,
  subject,
}: {
  day: PlanDay;
  index: number;
  isToday: boolean;
  subject: string;
}) {
  return (
    <MotiView
      from={{ opacity: 0, translateY: 10 }}
      animate={{ opacity: 1, translateY: 0 }}
      transition={{ type: "timing", duration: 300, delay: index * 60 }}
    >
      <Card className={`mb-3 ${isToday ? "border-2 border-primary" : ""}`}>
        <View className="flex-row justify-between items-center mb-2">
          <Text className="font-bold text-ink">День {day.day_index}</Text>
          {day.status === "complete" ? (
            <Text className="text-success text-sm font-medium">Готово</Text>
          ) : isToday ? (
            <Text className="text-primary text-sm font-medium">Сегодня</Text>
          ) : (
            <Text className="text-slate-400 text-sm">Заблокировано</Text>
          )}
        </View>
        <Text className="text-slate-500 text-sm mb-3">{day.summary}</Text>
        <View className="flex-row flex-wrap gap-2">
          {day.topics.map((t, i) => (
            <View key={i} className="bg-slate-100 rounded-lg px-3 py-1">
              <Text className="text-slate-600 text-xs">{t.minutes} мин</Text>
            </View>
          ))}
        </View>
        {isToday && (
          <Button
            label="Начать"
            size="sm"
            className="mt-3"
            onPress={() => {
              const topicId = day.topics[0]?.topic_id;
              if (topicId) router.push(`/lesson/${subject}/${topicId}`);
            }}
          />
        )}
      </Card>
    </MotiView>
  );
}

export default function PlanScreen() {
  const { subject } = useLocalSearchParams<{ subject: string }>();
  const { data: plan, isLoading } = useCurrentPlan(subject);

  if (isLoading || !plan) {
    return (
      <View className="flex-1 bg-surface items-center justify-center">
        <Text className="text-slate-400">Загружаем план...</Text>
      </View>
    );
  }

  const todayIndex = plan.days.findIndex((d) => d.status !== "complete");
  const activeDayIndex = todayIndex === -1 ? 0 : todayIndex;

  return (
    <View className="flex-1 bg-surface">
      <View className="px-6 pt-14 pb-4">
        <Text className="text-2xl font-bold text-ink">Твой план</Text>
        <Text className="text-slate-400 mt-1">14 дней до заметного прогресса</Text>
      </View>
      <FlatList
        data={plan.days}
        keyExtractor={(d) => String(d.day_index)}
        contentContainerStyle={{ padding: 24, paddingTop: 0 }}
        renderItem={({ item, index }) => (
          <DayCard
            day={item}
            index={index}
            isToday={index === activeDayIndex}
            subject={subject}
          />
        )}
      />
    </View>
  );
}
