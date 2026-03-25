import cors from "cors";
import express from "express";
import helmet from "helmet";

import { healthController } from "./controllers/healthController.js";
import { LabelController } from "./controllers/labelController.js";
import { ProjectController } from "./controllers/projectController.js";
import { TaskController } from "./controllers/taskController.js";
import { pool } from "./db/pool.js";
import { LabelRepository } from "./repositories/LabelRepository.js";
import { ProjectRepository } from "./repositories/ProjectRepository.js";
import { TaskRepository } from "./repositories/TaskRepository.js";
import { buildLabelRoutes } from "./routes/labelRoutes.js";
import { buildProjectRoutes } from "./routes/projectRoutes.js";
import { buildTaskRoutes } from "./routes/taskRoutes.js";
import { BoardService } from "./services/BoardService.js";

export function buildApp() {
  const app = express();

  app.disable("x-powered-by");
  app.use(helmet());
  app.use(
    cors({
      origin: process.env.CLIENT_ORIGIN || "http://localhost:5173",
    })
  );
  app.use(express.json({ limit: "20kb" }));

  const boardService = new BoardService(
    new ProjectRepository(pool),
    new TaskRepository(pool),
    new LabelRepository(pool)
  );

  app.get("/api/health", healthController);
  app.use("/api/projects", buildProjectRoutes(new ProjectController(boardService)));
  app.use("/api/tasks", buildTaskRoutes(new TaskController(boardService)));
  app.use("/api/labels", buildLabelRoutes(new LabelController(boardService)));

  app.use((_request, response) => {
    response.status(404).json({ error: "Not found" });
  });

  app.use((error, _request, response, _next) => {
    response.status(400).json({ error: error.message || "Unexpected error" });
  });

  return app;
}

