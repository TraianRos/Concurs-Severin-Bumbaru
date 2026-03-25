import { Router } from "express";

export function buildProjectRoutes(projectController) {
  const router = Router();
  router.get("/", projectController.list);
  router.post("/", projectController.create);
  return router;
}

