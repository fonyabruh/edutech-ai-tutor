import { ScrollView, Text, View } from "react-native";
import { router } from "expo-router";
import { Card } from "@/components/ui";
import { useMySubjects } from "@/hooks/api/useMe";
import { SUBJECTS } from "@/lib/subjects";

export default function DiagnosticPicker() {
  const { data: mySubjects } = useMySubjects();
  const enrolled = new Set((mySubjects ?? []).map((s) => s.code));
  const list = enrolled.size > 0 ? SUBJECTS.filter((s) => enrolled.has(s.code)) : SUBJECTS;

  return (
    <ScrollView className="flex-1 bg-surface" contentContainerStyle={{ padding: 24, paddingTop: 60 }}>
      <Text className="text-2xl font-bold text-ink mb-1">Диагностика</Text>
      <Text className="text-slate-400 mb-6">Выбери предмет для диагностики</Text>
      <View className="gap-4">
        {list.map((s) => (
          <Card key={s.code} onPress={() => router.push(`/diagnostic/${s.code}`)}>
            <Text className="font-semibold text-ink text-lg">{s.label}</Text>
            <Text className="text-slate-400 text-sm mt-1">Пройди тест для оценки уровня</Text>
          </Card>
        ))}
      </View>
    </ScrollView>
  );
}
