import { Pressable, Text, View } from "react-native";
import { MotiView } from "moti";

function tileColor(value: number) {
  if (value >= 0.8) return "bg-success";
  if (value >= 0.6) return "bg-primary";
  if (value >= 0.4) return "bg-yellow-400";
  return "bg-red-400";
}

interface HeatmapProps {
  tiles: Array<{ id: string | number; label: string; value: number }>;
  onPress?: (id: string | number) => void;
}

export function Heatmap({ tiles, onPress }: HeatmapProps) {
  return (
    <View className="flex-row flex-wrap gap-2">
      {tiles.map((tile, index) => (
        <MotiView
          key={tile.id}
          from={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ type: "timing", duration: 300, delay: index * 40 }}
        >
          <Pressable onPress={() => onPress?.(tile.id)} className="items-center">
            <View className={`w-14 h-14 rounded-lg ${tileColor(tile.value)}`} />
            <Text className="text-xs text-slate-500 mt-2 w-14 text-center" numberOfLines={1}>
              {tile.label}
            </Text>
          </Pressable>
        </MotiView>
      ))}
    </View>
  );
}
