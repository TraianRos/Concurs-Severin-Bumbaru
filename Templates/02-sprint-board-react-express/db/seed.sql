INSERT INTO projects (name, description) VALUES
('Contest Prep', 'Mini board for hackathon practice'),
('UI Cleanup', 'Tasks for the frontend refresh');

INSERT INTO labels (name, color) VALUES
('api', '#005f73'),
('ui', '#9b2226'),
('db', '#ee9b00');

INSERT INTO tasks (project_id, title, description, status, due_date) VALUES
(1, 'Design entities', 'Create the initial project and task tables', 'todo', '2026-04-04'),
(1, 'Write health route', 'Expose a simple Express health endpoint', 'doing', '2026-04-05'),
(2, 'Refine layout', 'Polish the board columns and task cards', 'done', '2026-04-02');

INSERT INTO task_labels (task_id, label_id) VALUES
(1, 3),
(2, 1),
(3, 2);

