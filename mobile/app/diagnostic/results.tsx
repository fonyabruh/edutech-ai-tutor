import { ScrollView, Text, View } from "react-native";
import { router, useLocalSearchParams } from "expo-router";
import { MotiView } from "moti";
import { Button, Card } from "@/components/ui";
import { useDiagnosticResult } from "@/hooks/api/useDiagnostic";
import { useGeneratePlan } from "@/hooks/api/usePlan";

export default function DiagnosticResults() {
  const { subject } = useLocalSearchParams<{ subject: string }>();
  const { data: result, isLoading } = useDiagnosticResult(subject);
  const generatePlan = useGeneratePlan();

  if (isLoading || !result) {
    return (
      <View className="flex-1 bg-surface items-center justify-center">
        <Text className="text-slate-400">Загружаем результаты...</Text>
      </View>
    );
  }

  const handleShowPlan = async () => {
    await generatePlan.mutateAsync(subject);
    router.push(`/plan/${subject}`);
  };

  return (
    <ScrollView className="flex-1 bg-surface" contentContainerStyle={{ padding: 24, paddingBottom: 48 }}>
      <MotiView from={{ opacity: 0, translateY: 20 }} animate={{ opacity: 1, translateY: 0 }} transition={{ type: "timing", duration: 500 }}>
        <Text className="text-2xl font-bold text-ink mb-2">Вот что я узнал про тебя</Text>
      </MotiView>

      <MotiView from={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ type: "timing", duration: 500, delay: 200 }}>
        <Card className="mt-4 items-center gap-1">
          <Text className="text-6xl font-bold text-primary">{result.estimated_score ?? "—"}</Text>
          <Text className="text-slate-400 text-sm">баллов прогноз</Text>
        </Card>
      </MotiView>

      {result.llm_summary ? (
        <MotiView from={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ type: "timing", duration: 500, delay: 400 }}>
          <Card className="mt-4">
            <Text className="text-ink leading-6">{result.llm_summary}</Text>
          </Card>
        </MotiView>
      ) : null}

      {(result.priority_skills ?? []).length > 0 ? (
        <MotiView from={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ type: "timing", duration: 500, delay: 500 }}>
          <Text className="text-lg font-semibold text-ink mt-6 mb-3">Приоритетные навыки</Text>
          <Card>
            <View className="gap-2">
              {result.priority_skills.map((skill, i) => (
                <View key={i} className="flex-row gap-2">
                  <Text className="text-primary font-bold">{i + 1}.</Text>
                  <Text className="text-ink flex-1">{skill}</Text>
                </View>
              ))}
            </View>
          </Card>
        </MotiView>
      ) : null}

      {(result.weak_topics ?? []).length > 0 ? (
        <MotiView from={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ type: "timing", duration: 500, delay: 600 }}>
          <Text className="text-lg font-semibold text-ink mt-6 mb-3">Главные пробелы</Text>
          <View className="gap-3">
            {(result.weak_topics ?? []).slice(0, 5).map((t, i) => (
              <Card key={i}>
                <Text className="text-slate-500 text-sm">Тема #{t.topic_id}</Text>
                {t.comment ? <Text className="text-ink mt-1">{t.comment}</Text> : null}
              </Card>
            ))}
          </View>
        </MotiView>
      ) : null}

      <Button
        label="Покажи мой план"
        onPress={handleShowPlan}
        loading={generatePlan.isPending}
        className="mt-8"
      />
    </ScrollView>
  );
}
