import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/AppShell";

export const Route = createFileRoute("/")({
  component: Index,
  head: () => ({
    meta: [
      { title: "AskDoc — Ask your documents" },
      {
        name: "description",
        content:
          "Upload PDFs and text documents and ask grounded questions with page-level citations.",
      },
    ],
  }),
});

function Index() {
  return <AppShell />;
}
