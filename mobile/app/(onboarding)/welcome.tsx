import { MotiText, MotiView } from "moti";
import { Text, View } from "react-native";
import { Button } from "@/components/ui";
import { router } from "expo-router";
import { api } from "@/lib/api";
import { setToken, storage } from "@/lib/storage";

export default function Welcome() {
  return (
    <View className="flex-1 bg-surface px-6 justify-between py-16">
      <MotiView
        from={{ opacity: 0, translateY: 20 }}
        animate={{ opacity: 1, translateY: 0 }}
        transition={{ type: "timing", duration: 600 }}
        className="gap-4"
      >
        <Text className="text-5xl font-bold text-ink">Привет.</Text>
        <MotiView
          from={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ type: "timing", duration: 600, delay: 300 }}
        >
          <Text className="text-xl text-slate-500 leading-8">
            Я помогу тебе подготовиться к экзамену так, чтобы ты понимал, почему ошибаешься —
            а не просто видел галочку.
          </Text>
        </MotiView>
      </MotiView>

      <MotiView
        from={{ opacity: 0, translateY: 10 }}
        animate={{ opacity: 1, translateY: 0 }}
        transition={{ type: "timing", duration: 500, delay: 700 }}
        className="items-center gap-6"
      >
        <Text className="text-6xl">🧠</Text>
        <Button
          label="Начнём"
          onPress={() => router.push("/(onboarding)/grade")}
          size="lg"
          className="w-full"
        />
        {__DEV__ && (
          <Button
            label="Войти как демо (dev)"
            variant="ghost"
            size="sm"
            onPress={async () => {
              storage.set("device_id", "demo-jury-001");
              const { data } = await api.post("/auth/anonymous", { device_id: "demo-jury-001" });
              setToken(data.access_token);
              router.replace("/(tabs)/");
            }}
          />
        )}
      </MotiView>
    </View>
  );
}
