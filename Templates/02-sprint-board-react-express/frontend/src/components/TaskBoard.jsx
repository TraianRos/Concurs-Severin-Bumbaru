const columns = ["todo", "doing", "done"];

export function TaskBoard({ tasks, onChangeStatus, onDelete }) {
  return (
    <section className="board-shell">
      {columns.map((status) => (
        <article className="board-column" key={status}>
          <header>
            <h2>{status}</h2>
          </header>

          <div className="task-stack">
            {tasks
              .filter((task) => task.status === status)
              .map((task) => (
                <div className="task-card" key={task.id}>
                  <strong>{task.title}</strong>
                  <p>{task.description}</p>
                  <span>{task.project_name}</span>

                  <div className="task-actions">
                    <select
                      value={task.status}
                      onChange={(event) => onChangeStatus(task.id, event.target.value)}
                      aria-label={`Change status for ${task.title}`}
                    >
                      {columns.map((value) => (
                        <option key={value} value={value}>
                          {value}
                        </option>
                      ))}
                    </select>
                    <button type="button" className="ghost-button" onClick={() => onDelete(task.id)}>
                      Delete
                    </button>
                  </div>
                </div>
              ))}
          </div>
        </article>
      ))}
    </section>
  );
}

