import { Text, View } from "react-native";
import { Button } from "./Button";

interface EmptyStateProps {
  icon?: string;
  message: string;
  action?: { label: string; onPress: () => void };
}

export function EmptyState({ icon = "📭", message, action }: EmptyStateProps) {
  return (
    <View className="flex-1 items-center justify-center gap-4 px-6">
      <Text className="text-4xl">{icon}</Text>
      <Text className="text-ink text-center">{message}</Text>
      {action && <Button label={action.label} onPress={action.onPress} variant="secondary" />}
    </View>
  );
}
