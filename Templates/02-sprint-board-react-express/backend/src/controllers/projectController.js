export class ProjectController {
  constructor(service) {
    this.service = service;
  }

  list = async (_request, response, next) => {
    try {
      response.json(await this.service.listProjects());
    } catch (error) {
      next(error);
    }
  };

  create = async (request, response, next) => {
    try {
      response.status(201).json(await this.service.createProject(request.body));
    } catch (error) {
      next(error);
    }
  };
}

