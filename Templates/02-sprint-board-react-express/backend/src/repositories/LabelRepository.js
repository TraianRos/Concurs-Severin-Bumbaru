export class LabelRepository {
  constructor(pool) {
    this.pool = pool;
  }

  async all() {
    const result = await this.pool.query("SELECT id, name, color FROM labels ORDER BY name");
    return result.rows;
  }
}

