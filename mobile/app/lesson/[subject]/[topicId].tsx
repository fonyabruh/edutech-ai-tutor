import { useEffect, useRef, useState } from "react";
import { Pressable, ScrollView, Text, View } from "react-native";
import { router, useLocalSearchParams } from "expo-router";
import { MotiView } from "moti";
import { Button, Card, LoadingDots, MarkdownView } from "@/components/ui";
import { SessionSummary } from "@/components/lesson/SessionSummary";
import { TaskRenderer } from "@/components/task/TaskRenderer";
import { useAnswerLesson, useFinishLesson, useStartLesson } from "@/hooks/api/useLesson";
import { useLLMStream } from "@/hooks/useLLMStream";
import type { LessonResult, Task } from "@/lib/types";

type Stage = "theory" | "task" | "feedback" | "explanation" | "summary";

export default function LessonScreen() {
  const { subject, topicId } = useLocalSearchParams<{ subject: string; topicId: string }>();
  const startLesson = useStartLesson();
  const answerLesson = useAnswerLesson();
  const finishLesson = useFinishLesson();
  const { text: streamText, isStreaming, start: startStream, reset: resetStream } = useLLMStream();

  const [lessonId, setLessonId] = useState<string | null>(null);
  const [theoryMd, setTheoryMd] = useState("");
  const [tasks, setTasks] = useState<Task[]>([]);
  const [taskIdx, setTaskIdx] = useState(0);
  const [stage, setStage] = useState<Stage>("theory");
  const [lastAnswer, setLastAnswer] = useState("");
  const [currentAnswer, setCurrentAnswer] = useState("");
  const [isCorrect, setIsCorrect] = useState(false);
  const [summary, setSummary] = useState<LessonResult | null>(null);

  useEffect(() => {
    startLesson.mutateAsync({ subject_code: subject, topic_id: Number(topicId) }).then((d) => {
      setLessonId(d.lesson_id);
      setTheoryMd(d.theory_md);
      setTasks(d.tasks);
    });
  }, []);

  const handleSubmitAnswer = async () => {
    if (!lessonId || !tasks[taskIdx]) return;
    const result = await answerLesson.mutateAsync({
      lesson_id: lessonId,
      task_id: tasks[taskIdx].id,
      user_answer: currentAnswer,
    });
    setIsCorrect(result.is_correct);
    setLastAnswer(currentAnswer);
    setStage("feedback");
    if (!result.is_correct) {
      setTimeout(() => {
        setStage("explanation");
        startStream("/lesson/explain", { task_id: tasks[taskIdx].id, user_answer: currentAnswer });
      }, 1000);
    } else {
      setTimeout(() => nextTask(), 1500);
    }
  };

  const nextTask = async () => {
    resetStream();
    if (taskIdx + 1 >= tasks.length) {
      const s = await finishLesson.mutateAsync(lessonId!);
      setSummary(s);
      setStage("summary");
    } else {
      setTaskIdx((i) => i + 1);
      setCurrentAnswer("");
      setStage("task");
    }
  };

  if (stage === "theory") {
    return (
      <ScrollView className="flex-1 bg-surface" contentContainerStyle={{ padding: 24, paddingTop: 60 }}>
        <Text className="text-2xl font-bold text-ink mb-4">Теория</Text>
        <Card><MarkdownView content={theoryMd} /></Card>
        <Button label="Понял, давай задачи" onPress={() => setStage("task")} className="mt-6" />
      </ScrollView>
    );
  }

  if (stage === "summary" && summary) {
    return (
      <SessionSummary
        summary={summary}
        onHome={() => router.replace("/(tabs)/")}
        onMore={() => router.back()}
      />
    );
  }

  const currentTask = tasks[taskIdx];

  return (
    <View className="flex-1 bg-surface">
      <View className="px-6 pt-14 pb-2 flex-row justify-between">
        <Text className="text-slate-400">Задача {taskIdx + 1}/{tasks.length}</Text>
      </View>

      <ScrollView className="flex-1 px-6" contentContainerStyle={{ paddingBottom: 140 }}>
        {currentTask && (
          <MotiView key={taskIdx} from={{ opacity: 0, translateY: 12 }} animate={{ opacity: 1, translateY: 0 }}>
            <Card className="mt-2">
              <TaskRenderer task={currentTask} onAnswer={setCurrentAnswer} />
            </Card>
          </MotiView>
        )}

        {stage === "feedback" && (
          <MotiView from={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ type: "timing", duration: 300 }}>
            <Card className={`mt-4 ${isCorrect ? "border-l-4 border-success" : "border-l-4 border-danger"}`}>
              <Text className={`font-bold text-lg ${isCorrect ? "text-success" : "text-danger"}`}>
                {isCorrect ? "Правильно! +10 XP" : "Неверно..."}
              </Text>
            </Card>
          </MotiView>
        )}

        {stage === "explanation" && (
          <MotiView from={{ opacity: 0, translateY: 20 }} animate={{ opacity: 1, translateY: 0 }} transition={{ type: "timing", duration: 400 }}>
            <Card className="mt-4 gap-3">
              <View className="flex-row items-center gap-2">
                <Text className="text-2xl">🤖</Text>
                <Text className="font-semibold text-ink">AI-репетитор</Text>
                {isStreaming && <LoadingDots />}
              </View>
              <MarkdownView content={streamText || "Разбираю твою ошибку..."} />
              {!isStreaming && streamText && (
                <Button label="Понял" onPress={nextTask} variant="secondary" size="sm" />
              )}
            </Card>
          </MotiView>
        )}
      </ScrollView>

      {stage === "task" && (
        <View className="absolute bottom-0 left-0 right-0 bg-surface px-6 pb-10 pt-4">
          <Button
            label="Ответить"
            onPress={handleSubmitAnswer}
            disabled={!currentAnswer}
            loading={answerLesson.isPending}
          />
        </View>
      )}
    </View>
  );
}
