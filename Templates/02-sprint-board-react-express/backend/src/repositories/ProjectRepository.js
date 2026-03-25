export class ProjectRepository {
  constructor(pool) {
    this.pool = pool;
  }

  async all() {
    const result = await this.pool.query(
      "SELECT id, name, description, created_at FROM projects ORDER BY created_at DESC"
    );
    return result.rows;
  }

  async create({ name, description }) {
    const result = await this.pool.query(
      "INSERT INTO projects (name, description) VALUES ($1, $2) RETURNING id, name, description, created_at",
      [name, description]
    );
    return result.rows[0];
  }
}

