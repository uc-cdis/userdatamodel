ALTER TABLE research_group ALTER COLUMN name TYPE varchar;
ALTER TABLE user_access RENAME TO access_privilege;
ALTER TABLE access_privilege
    ADD COLUMN group_id int;

ALTER TABLE access_privilege ADD CONSTRAINT group_fk FOREIGN KEY (group_id) REFERENCES research_group (id) MATCH FULL;

ALTER TABLE access_privilege
  DROP CONSTRAINT IF EXISTS uniq_ua;

ALTER TABLE access_privilege
  ADD CONSTRAINT uniq_ap UNIQUE(user_id, group_id, project_id);

CREATE UNIQUE INDEX unique_group_project_id ON access_privilege (group_id, project_id) WHERE (user_id is null);
CREATE UNIQUE INDEX unique_user_project_id ON access_privilege (user_id, project_id) WHERE (group_id is null);
CREATE UNIQUE INDEX unique_user_group_id ON access_privilege (user_id, group_id) WHERE (project_id is null);
