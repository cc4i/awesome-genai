-- y}~8-R6hFF?;}ilG

DROP TABLE IF EXISTS threads;
CREATE TABLE threads (
    thread_id bigserial NOT NULL,
    display_name text NOT NULL,
    thread_type text,
    context text NOT NULL,
    instructions text NOT NULL,
    platform_ids  text[] NOT NULL,
    target_locations text[],
    created_at timestamptz NOT NULL,
    updated_at timestamptz
) ;
ALTER TABLE threads ADD PRIMARY KEY (thread_id);

DROP TABLE IF EXISTS jobs;
CREATE TABLE jobs (
    job_id text NOT NULL,
    thread_id bigint NOT NULL,
    keywords text[] NOT NULL,
    platform_id text NOT NULL,
    job_interval smallint,
    status text,
    created_at timestamptz NOT NULL,
    updated_at timestamptz
) ;
ALTER TABLE jobs ADD PRIMARY KEY (job_id);



DROP TABLE IF EXISTS platforms;
CREATE TABLE platforms (
    platform_id text NOT NULL,
    secret text,
    endpoint text,
    created_at timestamptz NOT NULL,
    updated_at timestamptz
) ;
ALTER TABLE platforms ADD PRIMARY KEY (platform_id);


DROP TABLE IF EXISTS posts;
CREATE TABLE posts (
    post_id text NOT NULL,
    thread_id bigint NOT NULL,
    platform_id text NOT NULL,
    parent_id text, --To be post_id if it's comment and which post_id refers to
    content text NOT NULL,
    summary text,
    engaged_content text,
    conent_type text NOT NULL, --Enum: "comment", "post"
    user_id text,
    hastags text[],
    likes integer,
    shares integer,
    comments integer,
    sentiment_score double precision,
    sentiment_magnitude double precision,
    sentiment_label text,
    status text NOT NULL, --Enum: "pending", "sentimented", "ignored", "generated"
    created_at timestamptz,
    scraped_at timestamptz NOT NULL,
    sentiment_at timestamptz,
    generated_at timestamptz, -- when the engaged content was generated
    updated_at timestamptz
) ;
ALTER TABLE posts ADD PRIMARY KEY (post_id);


DROP TABLE IF EXISTS sentiment_summary;
CREATE TABLE sentiment_summary (
    sentiment_id bigserial NOT NULL,
    thread_id bigint NOT NULL,
    platform_id text NOT NULL,
    sentiment_level double precision NOT NULL,
    created_at timestamptz NOT NULL,
    updated_at timestamptz
) ;
ALTER TABLE sentiment_summary ADD PRIMARY KEY (sentiment_id);


DROP TABLE IF EXISTS posts;
CREATE TABLE posts (
    post_id text NOT NULL,
    thread_id bigint NOT NULL,
    platform_id text NOT NULL,
    parent_id text, --To be post_id if it's comment and which post_id refers to
    content text NOT NULL,
    summary text,
    engaged_content text,
    conent_type text NOT NULL, --Enum: "comment", "post"
    user_id text,
    hastags text[],
    likes integer,
    shares integer,
    comments integer,
    sentiment_score double precision,
    sentiment_magnitude double precision,
    sentiment_label text,
    status text NOT NULL, --Enum: "pending", "processing", "sentimented", "ignored", "generated"
    created_at timestamptz,
    scraped_at timestamptz NOT NULL,
    sentiment_at timestamptz,
    generated_at timestamptz, -- when the engaged content was generated
    updated_at timestamptz
) ;
ALTER TABLE posts ADD PRIMARY KEY (post_id);


DROP TABLE IF EXISTS marked_blob;
CREATE TABLE marked_blob (
    blob_name text NOT NULL,
    ops_id text,
    created_at timestamptz NOT NULL

) ;
ALTER TABLE marked_blob ADD PRIMARY KEY (blob_name);


DROP TABLE IF EXISTS playbooks;
CREATE TABLE playbooks (
    playbook_id bigserial NOT NULL,
    display_name text NOT NULL,
    thread_id bigint NOT NULL,
    assessment JSONB NOT NULL,
    plan JSONB NOT NULL,
    created_at timestamptz NOT NULL,
    updated_at timestamptz
);
ALTER TABLE playbooks ADD PRIMARY KEY (playbook_id);