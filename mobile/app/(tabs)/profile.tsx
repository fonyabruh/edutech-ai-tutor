import { ScrollView, Text, View } from "react-native";
import { Card } from "@/components/ui";
import { useMe } from "@/hooks/api/useMe";

const GOAL_LABELS: Record<string, string> = {
  min: "Сдать на минимум",
  good: "Хороший балл",
  excellent: "Высокий балл (90+)",
};

const SUBJECT_NAMES: Record<string, string> = {
  math_base: "Математика",
  rus: "Русский язык",
  soc: "Обществознание",
};

export default function Profile() {
  const { data: user } = useMe();

  if (!user) return null;

  const subjects: string[] = (() => {
    try {
      return JSON.parse(user.subjects || "[]");
    } catch {
      return [];
    }
  })();

  return (
    <ScrollView className="flex-1 bg-surface" contentContainerStyle={{ padding: 24, paddingTop: 60 }}>
      <Text className="text-2xl font-bold text-ink mb-6">Профиль</Text>
      <View className="gap-4">
        <Card>
          <Text className="text-slate-400 text-sm">Класс</Text>
          <Text className="text-ink font-semibold mt-1">{user.grade ?? "Не указан"}</Text>
        </Card>
        <Card>
          <Text className="text-slate-400 text-sm">Экзамен</Text>
          <Text className="text-ink font-semibold mt-1">{user.exam ?? "Не указан"}</Text>
        </Card>
        <Card>
          <Text className="text-slate-400 text-sm">Цель</Text>
          <Text className="text-ink font-semibold mt-1">
            {user.goal ? GOAL_LABELS[user.goal] : "Не указана"}
          </Text>
        </Card>
        <Card>
          <Text className="text-slate-400 text-sm">Предметы</Text>
          <Text className="text-ink font-semibold mt-1">
            {subjects.map((c) => SUBJECT_NAMES[c] ?? c).join(", ") || "Не выбраны"}
          </Text>
        </Card>
      </View>
    </ScrollView>
  );
}
