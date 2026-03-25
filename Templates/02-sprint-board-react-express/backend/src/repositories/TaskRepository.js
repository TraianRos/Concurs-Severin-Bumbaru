export class TaskRepository {
  constructor(pool) {
    this.pool = pool;
  }

  async all() {
    const result = await this.pool.query(`
      SELECT
        t.id,
        t.title,
        t.description,
        t.status,
        t.due_date,
        p.name AS project_name,
        COALESCE(array_agg(l.id) FILTER (WHERE l.id IS NOT NULL), '{}') AS label_ids
      FROM tasks t
      JOIN projects p ON p.id = t.project_id
      LEFT JOIN task_labels tl ON tl.task_id = t.id
      LEFT JOIN labels l ON l.id = tl.label_id
      GROUP BY t.id, p.name
      ORDER BY t.created_at DESC
    `);
    return result.rows;
  }

  async create({ title, description, status, projectId, dueDate, labelIds }) {
    const client = await this.pool.connect();

    try {
      await client.query("BEGIN");
      const taskResult = await client.query(
        `
          INSERT INTO tasks (project_id, title, description, status, due_date)
          VALUES ($1, $2, $3, $4, $5)
          RETURNING id, project_id, title, description, status, due_date, created_at
        `,
        [projectId, title, description, status, dueDate || null]
      );

      for (const labelId of labelIds) {
        await client.query("INSERT INTO task_labels (task_id, label_id) VALUES ($1, $2)", [taskResult.rows[0].id, labelId]);
      }

      await client.query("COMMIT");
      return taskResult.rows[0];
    } catch (error) {
      await client.query("ROLLBACK");
      throw error;
    } finally {
      client.release();
    }
  }

  async updateStatus(taskId, status) {
    const result = await this.pool.query(
      "UPDATE tasks SET status = $1 WHERE id = $2 RETURNING id, status",
      [status, taskId]
    );
    return result.rows[0] || null;
  }

  async delete(taskId) {
    const result = await this.pool.query("DELETE FROM tasks WHERE id = $1 RETURNING id", [taskId]);
    return result.rows[0] || null;
  }
}

