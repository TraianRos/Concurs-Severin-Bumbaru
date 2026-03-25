import { expect, test } from "vitest";
import { render, screen } from "@testing-library/react";
import { TaskBoard } from "./TaskBoard";

test("renders grouped tasks", () => {
  render(
    <TaskBoard
      tasks={[{ id: 1, title: "Write docs", description: "Prepare README", project_name: "Prep", status: "todo" }]}
      onChangeStatus={() => {}}
      onDelete={() => {}}
    />
  );

  expect(screen.getByText("Write docs")).toBeInTheDocument();
});
