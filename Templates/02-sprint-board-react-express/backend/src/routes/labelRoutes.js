import { Router } from "express";

export function buildLabelRoutes(labelController) {
  const router = Router();
  router.get("/", labelController.list);
  return router;
}

