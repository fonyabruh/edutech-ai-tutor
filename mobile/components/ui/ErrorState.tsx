import { Text, View } from "react-native";
import { Button } from "./Button";

interface ErrorStateProps {
  message?: string;
  onRetry?: () => void;
}

export function ErrorState({ message = "Что-то пошло не так", onRetry }: ErrorStateProps) {
  return (
    <View className="flex-1 items-center justify-center gap-4 px-6">
      <Text className="text-4xl">⚠️</Text>
      <Text className="text-ink text-center">{message}</Text>
      {onRetry && <Button label="Попробовать снова" onPress={onRetry} variant="secondary" />}
    </View>
  );
}
