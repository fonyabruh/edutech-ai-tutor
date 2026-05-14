import { useEffect } from "react";
import { View } from "react-native";
import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withTiming,
} from "react-native-reanimated";

interface Props {
  value: number; // 0..1
  className?: string;
}

export function ProgressBar({ value, className = "" }: Props) {
  const width = useSharedValue(0);

  useEffect(() => {
    width.value = withTiming(value, { duration: 400 });
  }, [value]);

  const animStyle = useAnimatedStyle(() => ({
    width: `${width.value * 100}%`,
  }));

  return (
    <View className={`h-2 bg-slate-200 rounded-full overflow-hidden ${className}`}>
      <Animated.View style={animStyle} className="h-full bg-primary rounded-full" />
    </View>
  );
}
