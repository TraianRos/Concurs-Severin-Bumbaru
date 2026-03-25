import { useState } from "react";

export function TaskForm({ projects, labels, onSubmit }) {
  const [form, setForm] = useState({
    title: "",
    description: "",
    status: "todo",
    projectId: "",
    dueDate: "",
    labelIds: [],
  });

  function handleCheckbox(labelId, checked) {
    setForm((current) => ({
      ...current,
      labelIds: checked
        ? [...current.labelIds, labelId]
        : current.labelIds.filter((value) => value !== labelId),
    }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    await onSubmit(form);
    setForm({
      title: "",
      description: "",
      status: "todo",
      projectId: "",
      dueDate: "",
      labelIds: [],
    });
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>New task</h2>
        <p>Create a minimal task with status and labels.</p>
      </div>

      <form className="stack-form" onSubmit={handleSubmit}>
        <label>
          <span>Title</span>
          <input
            value={form.title}
            onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))}
            required
          />
        </label>

        <label>
          <span>Description</span>
          <textarea
            value={form.description}
            onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))}
            required
          />
        </label>

        <label>
          <span>Project</span>
          <select
            value={form.projectId}
            onChange={(event) => setForm((current) => ({ ...current, projectId: event.target.value }))}
            required
          >
            <option value="">Select a project</option>
            {projects.map((project) => (
              <option key={project.id} value={project.id}>
                {project.name}
              </option>
            ))}
          </select>
        </label>

        <label>
          <span>Status</span>
          <select
            value={form.status}
            onChange={(event) => setForm((current) => ({ ...current, status: event.target.value }))}
          >
            <option value="todo">todo</option>
            <option value="doing">doing</option>
            <option value="done">done</option>
          </select>
        </label>

        <label>
          <span>Due date</span>
          <input
            type="date"
            value={form.dueDate}
            onChange={(event) => setForm((current) => ({ ...current, dueDate: event.target.value }))}
          />
        </label>

        <fieldset className="label-group">
          <legend>Labels</legend>
          {labels.map((label) => (
            <label key={label.id} className="checkbox-row">
              <input
                type="checkbox"
                checked={form.labelIds.includes(label.id)}
                onChange={(event) => handleCheckbox(label.id, event.target.checked)}
              />
              <span>{label.name}</span>
            </label>
          ))}
        </fieldset>

        <button type="submit">Create task</button>
      </form>
    </section>
  );
}

