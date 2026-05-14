import { useState } from "react";
import { TextInput, View } from "react-native";
import { TaskStatement } from "./TaskStatement";
import type { Task } from "@/lib/types";

interface Props {
  task: Task;
  onAnswer: (answer: string) => void;
  numeric?: boolean;
}

export function TaskShortAnswer({ task, onAnswer, numeric = false }: Props) {
  const [value, setValue] = useState("");

  return (
    <View className="gap-4">
      <TaskStatement statement={task.statement_md} />
      <TextInput
        className="border border-slate-300 rounded-xl px-4 py-3 text-ink text-base bg-white"
        value={value}
        onChangeText={(t) => {
          setValue(t);
          onAnswer(t);
        }}
        keyboardType={numeric ? "numeric" : "default"}
        placeholder="Введи ответ..."
        placeholderTextColor="#94a3b8"
        returnKeyType="done"
      />
    </View>
  );
}
