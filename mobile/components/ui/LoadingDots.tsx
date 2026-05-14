import { MotiView } from "moti";
import { View } from "react-native";

export function LoadingDots() {
  return (
    <View className="flex-row gap-1 items-center">
      {[0, 1, 2].map((i) => (
        <MotiView
          key={i}
          from={{ opacity: 0.3, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ type: "timing", duration: 500, loop: true, delay: i * 150 }}
          className="w-2 h-2 rounded-full bg-primary"
        />
      ))}
    </View>
  );
}
