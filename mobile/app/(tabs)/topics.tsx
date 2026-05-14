import { useState } from "react";
import { FlatList, ScrollView, Text, TouchableOpacity, View } from "react-native";
import { router } from "expo-router";
import { Button, Card } from "@/components/ui";
import { useMySubjects } from "@/hooks/api/useMe";
import { useTopics } from "@/hooks/api/useTopics";

function masteryColor(v: number) {
  if (v >= 0.8) return "bg-success";
  if (v >= 0.6) return "bg-primary";
  if (v >= 0.4) return "bg-yellow-400";
  return "bg-red-400";
}

export default function Topics() {
  const { data: subjects } = useMySubjects();
  const userSubjects = subjects ?? [];
  const [activeCode, setActiveCode] = useState(userSubjects[0]?.code ?? "math_base");
  const { data: topics, isLoading } = useTopics(activeCode);

  return (
    <View className="flex-1 bg-surface">
      <View className="px-6 pt-14 pb-2">
        <Text className="text-2xl font-bold text-ink mb-4">Темы</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          <View className="flex-row gap-2">
            {userSubjects.map((s) => (
              <TouchableOpacity
                key={s.code}
                onPress={() => setActiveCode(s.code)}
                className={`px-4 py-2 rounded-full ${activeCode === s.code ? "bg-primary" : "bg-slate-200"}`}
              >
                <Text className={activeCode === s.code ? "text-white text-sm font-medium" : "text-ink text-sm"}>
                  {s.name}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </ScrollView>
      </View>

      {isLoading ? (
        <View className="flex-1 items-center justify-center">
          <Text className="text-slate-400">Загрузка...</Text>
        </View>
      ) : !topics || topics.length === 0 ? (
        <ScrollView contentContainerStyle={{ padding: 24 }}>
          <Button
            label="Начать диагностику"
            onPress={() => router.push(`/diagnostic/${activeCode}`)}
            variant="secondary"
            size="sm"
            className="mb-4"
          />
          <Card>
            <Text className="text-slate-400 text-center py-4">
              Пройди диагностику, чтобы увидеть карту тем
            </Text>
          </Card>
        </ScrollView>
      ) : (
        <FlatList
          data={topics}
          keyExtractor={(t) => String(t.id)}
          contentContainerStyle={{ padding: 24, paddingTop: 12 }}
          ListHeaderComponent={
            <View className="flex-row flex-wrap gap-2 mb-4">
              {topics.map((t) => (
                <View
                  key={t.id}
                  className={`w-8 h-8 rounded-md ${masteryColor(t.mastery)}`}
                />
              ))}
            </View>
          }
          renderItem={({ item: t }) => (
            <Card className="mb-3">
              <View className="flex-row items-center gap-3">
                <View className={`w-3 h-3 rounded-full ${masteryColor(t.mastery)}`} />
                <View className="flex-1">
                  <Text className="text-ink font-medium text-sm">{t.name}</Text>
                  <Text className="text-slate-400 text-xs">{t.codifier_code}</Text>
                </View>
                <Text className="text-slate-400 text-xs">
                  {Math.round(t.mastery * 100)}%
                </Text>
              </View>
              <Button
                label="Тренировать"
                size="sm"
                variant="secondary"
                className="mt-2"
                onPress={() => router.push(`/lesson/${activeCode}/${t.id}`)}
              />
            </Card>
          )}
        />
      )}
    </View>
  );
}
