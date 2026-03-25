import test from "node:test";
import assert from "node:assert/strict";
import request from "supertest";

import { buildApp } from "../src/app.js";

test("health endpoint returns ok", async () => {
  const response = await request(buildApp()).get("/api/health");
  assert.equal(response.statusCode, 200);
  assert.equal(response.body.status, "ok");
});

