import { View } from "react-native";
import { MotiView } from "moti";

interface LoadingStateProps {
  rows?: number;
}

export function LoadingState({ rows = 3 }: LoadingStateProps) {
  return (
    <View>
      {Array.from({ length: rows }).map((_, i) => (
        <MotiView
          key={i}
          from={{ opacity: 0.4 }}
          animate={{ opacity: [0.4, 0.8, 0.4] }}
          transition={{ type: "timing", duration: 1000, loop: true }}
          className="rounded-xl h-16 bg-slate-200 mb-3"
        />
      ))}
    </View>
  );
}
