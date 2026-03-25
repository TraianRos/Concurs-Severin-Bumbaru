const API_URL = "http://localhost:4000/api";

async function request(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({ error: "Unexpected error" }));
    throw new Error(payload.error || "Unexpected error");
  }

  return response.json();
}

export const api = {
  getProjects: () => request("/projects"),
  createProject: (payload) => request("/projects", { method: "POST", body: JSON.stringify(payload) }),
  getTasks: () => request("/tasks"),
  createTask: (payload) => request("/tasks", { method: "POST", body: JSON.stringify(payload) }),
  updateTask: (taskId, payload) => request(`/tasks/${taskId}`, { method: "PATCH", body: JSON.stringify(payload) }),
  deleteTask: (taskId) => request(`/tasks/${taskId}`, { method: "DELETE" }),
  getLabels: () => request("/labels"),
};

