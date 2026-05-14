import { useState } from "react";
import { View } from "react-native";
import { Chip } from "@/components/ui";
import { TaskStatement } from "./TaskStatement";
import type { Task } from "@/lib/types";

interface Props {
  task: Task;
  onAnswer: (answer: string) => void;
}

export function TaskMultiChoice({ task, onAnswer }: Props) {
  const [selected, setSelected] = useState<string | null>(null);

  const choose = (opt: string) => {
    setSelected(opt);
    onAnswer(opt);
  };

  return (
    <View className="gap-3">
      <TaskStatement statement={task.statement_md} />
      {(task.options ?? []).map((opt, i) => (
        <Chip
          key={`${i}-${opt}`}
          label={opt}
          selected={selected === opt}
          onPress={() => choose(opt)}
          className="w-full justify-start px-5 py-4"
        />
      ))}
    </View>
  );
}
