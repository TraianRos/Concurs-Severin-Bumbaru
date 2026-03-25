import { useEffect, useState } from "react";
import { ProjectList } from "../components/ProjectList";
import { TaskBoard } from "../components/TaskBoard";
import { TaskForm } from "../components/TaskForm";
import { api } from "../services/api";

export function DashboardPage() {
  const [projects, setProjects] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [labels, setLabels] = useState([]);
  const [message, setMessage] = useState("Loading board...");

  async function loadData() {
    const [projectRows, taskRows, labelRows] = await Promise.all([
      api.getProjects(),
      api.getTasks(),
      api.getLabels(),
    ]);

    setProjects(projectRows);
    setTasks(taskRows);
    setLabels(labelRows);
    setMessage("Board ready.");
  }

  useEffect(() => {
    loadData().catch(() => setMessage("Could not load data."));
  }, []);

  async function handleProjectSubmit(payload) {
    await api.createProject(payload);
    await loadData();
    setMessage("Project created.");
  }

  async function handleTaskSubmit(payload) {
    await api.createTask(payload);
    await loadData();
    setMessage("Task created.");
  }

  async function handleStatusChange(taskId, status) {
    await api.updateTask(taskId, { status });
    await loadData();
    setMessage("Task updated.");
  }

  async function handleDelete(taskId) {
    await api.deleteTask(taskId);
    await loadData();
    setMessage("Task deleted.");
  }

  return (
    <div className="app-shell">
      <header className="hero">
        <div>
          <p className="eyebrow">SprintBoard</p>
          <h1>Project tasks without dashboard clutter.</h1>
        </div>
        <p className="hero-copy">{message}</p>
      </header>

      <section className="workspace">
        <ProjectList projects={projects} onCreate={handleProjectSubmit} />
        <TaskForm projects={projects} labels={labels} onSubmit={handleTaskSubmit} />
      </section>

      <TaskBoard tasks={tasks} labels={labels} onChangeStatus={handleStatusChange} onDelete={handleDelete} />
    </div>
  );
}

