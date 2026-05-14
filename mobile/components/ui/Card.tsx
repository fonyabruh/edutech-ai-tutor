import { Pressable, View } from "react-native";

interface Props {
  children: React.ReactNode;
  onPress?: () => void;
  className?: string;
}

export function Card({ children, onPress, className = "" }: Props) {
  const base = `bg-white rounded-2xl p-4 shadow-sm ${className}`;
  if (onPress) {
    return (
      <Pressable onPress={onPress} className={base}>
        {children}
      </Pressable>
    );
  }
  return <View className={base}>{children}</View>;
}
