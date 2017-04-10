ALTER TABLE user_access RENAME TO access_privilege;
ALTER TABLE access_privilege
    ADD COLUMN group_id int;

ALTER TABLE access_privilege ADD CONSTRAINT group_fk FOREIGN KEY (group_id) REFERENCES research_group (id) MATCH FULL;

ALTER TABLE access_privilege
  DROP CONSTRAINT uniq_ua;

ALTER TABLE access_privilege
  ADD CONSTRAINT uniq_ap UNIQUE(user_id, group_id, project_id);
