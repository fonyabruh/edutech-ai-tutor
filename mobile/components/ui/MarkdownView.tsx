import { Fragment } from "react";
import MathView from "react-native-math-view";
import { Text, View } from "react-native";

interface Props {
  content: string;
  className?: string;
}

function InlineText({ text }: { text: string }) {
  // split on math $...$ and bold **...**
  const parts = text.split(/([$]{1,2}[^$]+[$]{1,2}|\*\*[^*]+\*\*|`[^`]+`)/g);
  return (
    <Text className="text-ink text-base leading-6">
      {parts.map((p, i) => {
        if (p.startsWith("$$") && p.endsWith("$$")) {
          return <MathView key={i} math={p.slice(2, -2)} />;
        }
        if (p.startsWith("$") && p.endsWith("$")) {
          return <MathView key={i} math={p.slice(1, -1)} />;
        }
        if (p.startsWith("**") && p.endsWith("**")) {
          return <Text key={i} className="font-bold">{p.slice(2, -2)}</Text>;
        }
        if (p.startsWith("`") && p.endsWith("`")) {
          return <Text key={i} className="font-mono bg-slate-100 text-sm px-1 rounded">{p.slice(1, -1)}</Text>;
        }
        return <Fragment key={i}>{p}</Fragment>;
      })}
    </Text>
  );
}

function renderLine(line: string, idx: number) {
  if (!line.trim()) return <View key={idx} className="h-2" />;

  if (line.startsWith("### ")) {
    return <Text key={idx} className="text-base font-bold text-ink mt-3 mb-1">{line.slice(4)}</Text>;
  }
  if (line.startsWith("## ")) {
    return <Text key={idx} className="text-lg font-bold text-ink mt-4 mb-1">{line.slice(3)}</Text>;
  }
  if (line.startsWith("# ")) {
    return <Text key={idx} className="text-xl font-bold text-ink mt-4 mb-2">{line.slice(2)}</Text>;
  }
  if (line.startsWith("- ") || line.startsWith("* ")) {
    return (
      <View key={idx} className="flex-row gap-2 mb-1">
        <Text className="text-ink text-base mt-0.5">•</Text>
        <View className="flex-1"><InlineText text={line.slice(2)} /></View>
      </View>
    );
  }
  if (/^\d+\.\s/.test(line)) {
    const match = line.match(/^(\d+)\.\s(.*)$/);
    if (match) {
      return (
        <View key={idx} className="flex-row gap-2 mb-1">
          <Text className="text-ink text-base">{match[1]}.</Text>
          <View className="flex-1"><InlineText text={match[2]} /></View>
        </View>
      );
    }
  }
  if (line.startsWith("$$") && line.endsWith("$$")) {
    return <MathView key={idx} math={line.slice(2, -2)} style={{ marginVertical: 8 }} />;
  }

  return <View key={idx} className="mb-1"><InlineText text={line} /></View>;
}

export function MarkdownView({ content, className = "" }: Props) {
  const lines = content.split("\n");
  return (
    <View className={`gap-0.5 ${className}`}>
      {lines.map((line, i) => renderLine(line, i))}
    </View>
  );
}
