import { MarkdownView } from "@/components/ui";

export function TaskStatement({ statement }: { statement: string }) {
  return <MarkdownView content={statement} className="mb-4" />;
}
