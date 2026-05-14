import { ScrollView, Text, View } from "react-native";
import { router } from "expo-router";
import { MotiView } from "moti";
import { Button, Card, EmptyState } from "@/components/ui";
import { useMe, useMySubjects } from "@/hooks/api/useMe";
import { useCurrentPlan } from "@/hooks/api/usePlan";
import { SUBJECT_NAME } from "@/lib/subjects";

function TodayCard({ subjectCode }: { subjectCode: string }) {
  const { data: plan } = useCurrentPlan(subjectCode);
  if (!plan) return null;
  const todayIdx = plan.days.findIndex((d) => d.status !== "complete");
  const today = todayIdx >= 0 ? plan.days[todayIdx] : null;
  if (!today) return (
    <Card className="bg-success/10 border border-success/20">
      <Text className="font-semibold text-success">Готово на сегодня 🎉</Text>
      <Text className="text-slate-400 text-sm mt-1">Возвращайся завтра</Text>
    </Card>
  );
  return (
    <Card className="border-2 border-primary">
      <Text className="text-slate-400 text-xs mb-1">Сегодня в плане</Text>
      <Text className="font-bold text-ink text-base">{SUBJECT_NAME[subjectCode] ?? subjectCode}</Text>
      <Text className="text-slate-500 text-sm mt-1">{today.summary}</Text>
      <Button
        label="Начать"
        size="sm"
        className="mt-3"
        onPress={() => {
          const topicId = today.topics[0]?.topic_id;
          if (topicId) router.push(`/lesson/${subjectCode}/${topicId}`);
        }}
      />
    </Card>
  );
}

export default function Dashboard() {
  const { data: user } = useMe();
  const { data: subjects } = useMySubjects();
  const userSubjects = subjects ?? [];
  const subjectCodes: string[] = user?.subjects ? JSON.parse(user.subjects) : [];

  return (
    <ScrollView className="flex-1 bg-surface" contentContainerStyle={{ padding: 24, paddingTop: 60, gap: 16 }}>
      <MotiView from={{ opacity: 0, translateY: -10 }} animate={{ opacity: 1, translateY: 0 }}>
        <Text className="text-2xl font-bold text-ink">Привет!</Text>
        {(user?.streak ?? 0) > 0 && (
          <View className="flex-row items-center gap-2 mt-2">
            <Text className="text-2xl">🔥</Text>
            <Text className="text-slate-600 font-medium">День {user!.streak} подряд</Text>
          </View>
        )}
      </MotiView>

      {subjectCodes.length > 0 ? (
        subjectCodes.map((code) => <TodayCard key={code} subjectCode={code} />)
      ) : (
        <EmptyState
          icon="📚"
          message="Выбери предмет в онбординге"
        />
      )}

      <Text className="text-lg font-semibold text-ink mt-2">Предметы</Text>
      {userSubjects.length === 0 ? (
        <Card className="items-center gap-3">
          <Text className="text-ink font-semibold">Начни с диагностики</Text>
          <Text className="text-slate-400 text-sm text-center">Я пойму твой уровень и составлю план</Text>
          <Button label="Выбрать предмет" onPress={() => router.push("/diagnostic/picker")} size="sm" />
        </Card>
      ) : (
        userSubjects.map((s, i) => (
          <MotiView
            key={s.code}
            from={{ opacity: 0, translateY: 10 }}
            animate={{ opacity: 1, translateY: 0 }}
            transition={{ type: "timing", duration: 300, delay: i * 80 }}
          >
            <Card onPress={() => router.push(s.last_session_at ? `/plan/${s.code}` : `/diagnostic/${s.code}`)}>
              <View className="flex-row justify-between items-center">
                <Text className="font-semibold text-ink">{s.name}</Text>
                <Text className="text-primary text-sm font-medium">{Math.round((s.mastery_avg ?? 0) * 100)}%</Text>
              </View>
              <Text className="text-slate-400 text-sm mt-1">
                {s.last_session_at ? "Продолжить план" : "Начни с диагностики"}
              </Text>
              <View className="mt-2 h-1.5 bg-slate-200 rounded-full overflow-hidden">
                <View className="h-full bg-primary rounded-full" style={{ width: `${Math.round((s.mastery_avg ?? 0) * 100)}%` }} />
              </View>
            </Card>
          </MotiView>
        ))
      )}

      <Card onPress={() => router.push("/chat/index")} className="mt-2">
        <Text className="font-semibold text-ink">💬 Спроси у репетитора</Text>
        <Text className="text-slate-400 text-sm mt-1">Задай вопрос по любой теме</Text>
      </Card>
    </ScrollView>
  );
}
