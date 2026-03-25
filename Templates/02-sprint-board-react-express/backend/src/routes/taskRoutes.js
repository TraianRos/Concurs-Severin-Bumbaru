import { Router } from "express";

export function buildTaskRoutes(taskController) {
  const router = Router();
  router.get("/", taskController.list);
  router.post("/", taskController.create);
  router.patch("/:id", taskController.update);
  router.delete("/:id", taskController.delete);
  return router;
}

