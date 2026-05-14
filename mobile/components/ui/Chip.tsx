import { Pressable, Text } from "react-native";

interface Props {
  label: string;
  selected: boolean;
  onPress: () => void;
  className?: string;
}

export function Chip({ label, selected, onPress, className = "" }: Props) {
  return (
    <Pressable
      onPress={onPress}
      className={`px-4 py-2 rounded-full border ${
        selected ? "bg-primary border-primary" : "bg-white border-slate-300"
      } ${className}`}
    >
      <Text className={`text-sm font-medium ${selected ? "text-white" : "text-ink"}`}>
        {label}
      </Text>
    </Pressable>
  );
}
