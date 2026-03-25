export class BoardService {
  constructor(projectRepository, taskRepository, labelRepository) {
    this.projectRepository = projectRepository;
    this.taskRepository = taskRepository;
    this.labelRepository = labelRepository;
  }

  async listProjects() {
    return this.projectRepository.all();
  }

  async createProject(payload) {
    const name = String(payload.name || "").trim();
    const description = String(payload.description || "").trim();

    if (!name || !description) {
      throw new Error("Project name and description are required.");
    }

    return this.projectRepository.create({ name, description });
  }

  async listTasks() {
    return this.taskRepository.all();
  }

  async createTask(payload) {
    const title = String(payload.title || "").trim();
    const description = String(payload.description || "").trim();
    const status = String(payload.status || "todo").trim();
    const projectId = Number(payload.projectId || 0);
    const dueDate = String(payload.dueDate || "").trim();
    const labelIds = Array.isArray(payload.labelIds) ? payload.labelIds.map(Number).filter(Boolean) : [];

    if (!title || !description || projectId < 1) {
      throw new Error("Task title, description and project are required.");
    }

    if (!["todo", "doing", "done"].includes(status)) {
      throw new Error("Invalid status.");
    }

    return this.taskRepository.create({ title, description, status, projectId, dueDate, labelIds });
  }

  async updateTaskStatus(taskId, payload) {
    const status = String(payload.status || "").trim();
    if (!["todo", "doing", "done"].includes(status)) {
      throw new Error("Invalid status.");
    }

    const updated = await this.taskRepository.updateStatus(Number(taskId), status);
    if (!updated) {
      throw new Error("Task not found.");
    }

    return updated;
  }

  async deleteTask(taskId) {
    const deleted = await this.taskRepository.delete(Number(taskId));
    if (!deleted) {
      throw new Error("Task not found.");
    }

    return deleted;
  }

  async listLabels() {
    return this.labelRepository.all();
  }
}

