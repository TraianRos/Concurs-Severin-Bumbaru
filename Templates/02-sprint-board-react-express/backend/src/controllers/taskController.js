export class TaskController {
  constructor(service) {
    this.service = service;
  }

  list = async (_request, response, next) => {
    try {
      response.json(await this.service.listTasks());
    } catch (error) {
      next(error);
    }
  };

  create = async (request, response, next) => {
    try {
      response.status(201).json(await this.service.createTask(request.body));
    } catch (error) {
      next(error);
    }
  };

  update = async (request, response, next) => {
    try {
      response.json(await this.service.updateTaskStatus(request.params.id, request.body));
    } catch (error) {
      next(error);
    }
  };

  delete = async (request, response, next) => {
    try {
      response.json(await this.service.deleteTask(request.params.id));
    } catch (error) {
      next(error);
    }
  };
}

