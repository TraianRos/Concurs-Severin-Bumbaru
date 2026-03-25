export class LabelController {
  constructor(service) {
    this.service = service;
  }

  list = async (_request, response, next) => {
    try {
      response.json(await this.service.listLabels());
    } catch (error) {
      next(error);
    }
  };
}

