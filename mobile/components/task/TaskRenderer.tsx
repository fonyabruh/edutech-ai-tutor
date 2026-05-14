import type { Task } from "@/lib/types";
import { TaskMultiChoice } from "./TaskMultiChoice";
import { TaskShortAnswer } from "./TaskShortAnswer";

interface Props {
  task: Task;
  onAnswer: (answer: string) => void;
}

export function TaskRenderer({ task, onAnswer }: Props) {
  switch (task.type) {
    case "multi_choice":
      return <TaskMultiChoice task={task} onAnswer={onAnswer} />;
    case "numeric":
      return <TaskShortAnswer task={task} onAnswer={onAnswer} numeric />;
    default:
      return <TaskShortAnswer task={task} onAnswer={onAnswer} />;
  }
}
