
--This file contains a non-comprehensive list of table definitions for
--ORM classes defined in this repo

CREATE TABLE public."Group" (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    description character varying
);

CREATE TABLE public."User" (
    id integer NOT NULL,
    username character varying(255),
    id_from_idp character varying,
    display_name character varying,
    phone_number character varying,
    email character varying,
    _last_auth timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    idp_id integer,
    google_proxy_group_id character varying,
    department_id integer,
    active boolean,
    is_admin boolean DEFAULT false,
    additional_info jsonb DEFAULT '{}'::jsonb
);

CREATE TABLE public.access_privilege (
    id integer NOT NULL,
    user_id integer,
    group_id integer,
    project_id integer,
    privilege text[],
    provider_id integer,
    CONSTRAINT check_access_subject CHECK (((user_id IS NULL) OR (group_id IS NULL)))
);

CREATE TABLE public.authorization_provider (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    description character varying
);

CREATE TABLE public.bucket (
    id integer NOT NULL,
    name character varying,
    provider_id integer
);

CREATE TABLE public.cloud_provider (
    id integer NOT NULL,
    name character varying,
    endpoint character varying,
    backend character varying,
    description character varying,
    service character varying
);

CREATE TABLE public.department (
    id integer NOT NULL,
    name character varying(255),
    description character varying,
    org_id integer
);

CREATE TABLE public.google_proxy_group (
    id character varying(90) NOT NULL,
    email character varying NOT NULL
);

CREATE TABLE public.identity_provider (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    description character varying
);

CREATE TABLE public.organization (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    description character varying
);

CREATE TABLE public.project (
    id integer NOT NULL,
    name character varying NOT NULL,
    auth_id character varying,
    description character varying,
    parent_id integer,
    authz character varying
);

CREATE TABLE public.project_to_bucket (
    id integer NOT NULL,
    project_id integer,
    bucket_id integer,
    privilege text[]
);

CREATE TABLE public.storage_access (
    id integer NOT NULL,
    project_id integer,
    user_id integer,
    group_id integer,
    provider_id integer,
    max_objects bigint,
    max_size bigint,
    max_buckets integer,
    additional_info jsonb,
    CONSTRAINT check_storage_subject CHECK (((user_id IS NULL) OR (group_id IS NULL) OR (project_id IS NULL)))
);

CREATE TABLE public.tag (
    user_id integer NOT NULL,
    key character varying NOT NULL,
    value character varying
);
