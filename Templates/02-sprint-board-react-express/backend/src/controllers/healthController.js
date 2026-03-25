export const healthController = (_request, response) => {
  response.json({ status: "ok", app: "sprint-board" });
};

