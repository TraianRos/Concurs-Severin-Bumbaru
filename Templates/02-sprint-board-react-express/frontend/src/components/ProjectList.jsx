import { useState } from "react";

export function ProjectList({ projects, onCreate }) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    await onCreate({ name, description });
    setName("");
    setDescription("");
  }

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>Projects</h2>
        <p>Keep the top-level scope visible.</p>
      </div>

      <ul className="simple-list">
        {projects.map((project) => (
          <li key={project.id}>
            <strong>{project.name}</strong>
            <span>{project.description}</span>
          </li>
        ))}
      </ul>

      <form className="stack-form" onSubmit={handleSubmit}>
        <label>
          <span>Name</span>
          <input value={name} onChange={(event) => setName(event.target.value)} required />
        </label>
        <label>
          <span>Description</span>
          <textarea value={description} onChange={(event) => setDescription(event.target.value)} required />
        </label>
        <button type="submit">Create project</button>
      </form>
    </section>
  );
}

