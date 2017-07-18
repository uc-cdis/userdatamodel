ALTER TABLE access_privilege ADD CONSTRAINT check_access_subject CHECK (group_id is null or user_id is null);
ALTER TABLE storage_access ADD CONSTRAINT check_storage_subject CHECK (group_id is null or user_id is null or project_id is null);
