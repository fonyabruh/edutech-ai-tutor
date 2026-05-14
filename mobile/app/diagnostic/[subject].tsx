import { useEffect, useRef, useState } from "react";
import { ScrollView, Text, View } from "react-native";
import { router, useLocalSearchParams } from "expo-router";
import { MotiView } from "moti";
import { Button, Card, ProgressBar } from "@/components/ui";
import { TaskRenderer } from "@/components/task/TaskRenderer";
import { useAnswerDiagnostic, useFinishDiagnostic, useStartDiagnostic } from "@/hooks/api/useDiagnostic";
import type { Task } from "@/lib/types";

export default function DiagnosticScreen() {
  const { subject } = useLocalSearchParams<{ subject: string }>();
  const startMutation = useStartDiagnostic();
  const answerMutation = useAnswerDiagnostic();
  const finishMutation = useFinishDiagnostic();

  const [sessionId, setSessionId] = useState<string | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [currentAnswer, setCurrentAnswer] = useState<string | null>(null);
  const answered = useRef(false);

  useEffect(() => {
    startMutation.mutateAsync(subject).then((data) => {
      setSessionId(data.session_id);
      setTasks(data.tasks);
    });
  }, [subject]);

  const handleNext = async () => {
    if (!sessionId || answered.current) return;
    answered.current = true;
    await answerMutation.mutateAsync({
      session_id: sessionId,
      task_id: tasks[currentIdx].id,
      user_answer: currentAnswer,
    });

    if (currentIdx + 1 >= tasks.length) {
      await finishMutation.mutateAsync({ session_id: sessionId, subject_code: subject });
      router.replace(`/diagnostic/${subject}/analyzing`);
    } else {
      setCurrentIdx((i) => i + 1);
      setCurrentAnswer(null);
      answered.current = false;
    }
  };

  const handleSkip = async () => {
    if (!sessionId || answered.current) return;
    answered.current = true;
    await answerMutation.mutateAsync({
      session_id: sessionId,
      task_id: tasks[currentIdx].id,
      user_answer: null,
    });
    if (currentIdx + 1 >= tasks.length) {
      await finishMutation.mutateAsync({ session_id: sessionId, subject_code: subject });
      router.replace(`/diagnostic/${subject}/analyzing`);
    } else {
      setCurrentIdx((i) => i + 1);
      setCurrentAnswer(null);
      answered.current = false;
    }
  };

  if (!tasks.length) {
    return (
      <View className="flex-1 bg-surface items-center justify-center">
        <Text className="text-slate-400">Загружаем задачи...</Text>
      </View>
    );
  }

  const task = tasks[currentIdx];
  const progress = (currentIdx + 1) / tasks.length;

  return (
    <View className="flex-1 bg-surface">
      <View className="px-6 pt-14 pb-4 gap-2">
        <Text className="text-slate-400 text-sm">
          {currentIdx + 1} из {tasks.length}
        </Text>
        <ProgressBar value={progress} />
      </View>
      <ScrollView className="flex-1 px-6" contentContainerStyle={{ paddingBottom: 120 }}>
        <MotiView
          key={currentIdx}
          from={{ opacity: 0, translateY: 16 }}
          animate={{ opacity: 1, translateY: 0 }}
          transition={{ type: "timing", duration: 300 }}
        >
          <Card className="mt-4">
            <TaskRenderer task={task} onAnswer={setCurrentAnswer} />
          </Card>
        </MotiView>
      </ScrollView>
      <View className="absolute bottom-0 left-0 right-0 bg-surface px-6 pb-10 pt-4 gap-3">
        <Button
          label="Далее"
          onPress={handleNext}
          disabled={!currentAnswer}
          loading={answerMutation.isPending || finishMutation.isPending}
        />
        <Button label="Пропустить" onPress={handleSkip} variant="ghost" />
      </View>
    </View>
  );
}
