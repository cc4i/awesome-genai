
```json

{
    "display_name": "First order in Galaxa",
    "thread_type": "event",
    "context": "Rebeling is planning to mobilize troops and attack a planet, we must destroy their plan.",
    "instructions": "Monitoring all message from rebeling platforms",
    "platform_ids": ["twitter", "google_news"],
}


{
    "display_name": "Lucky release",
    "thread_type": "event",
    "context": "Find out if Lukcy is the best movie this year (2024) for Kids ",
    "instructions": "Monitoring all news online. Exclude news from Ads.",
    "platform_ids": ["google_news"],
}

```

```sql

insert into platforms (platform_id, secret, created_at)
values(
    'google-news', 
    'eyJzZXJwZXJfYXBpX2tleSI6IjFhOGNiYzRhYzM0OWVmYmRmOTExZGM1MTkzMGNiNjU3NmQ0NzgwZTQifQo=',
    now()
)
insert into platforms (platform_id, secret, created_at)
values(
    'google-search', 
    'eyJzZXJwZXJfYXBpX2tleSI6IjFhOGNiYzRhYzM0OWVmYmRmOTExZGM1MTkzMGNiNjU3NmQ0NzgwZTQifQo=',
    now()
)

-- scraping-job-{thread_id}-{platform_id}
insert into jobs (job_id, thread_id, keywords, platform_id, job_interval, created_at)
values(
    'scraping-job-1-google-news',
    1,
    '{"Star Wars", "Star Wars: Rebellion", "Star Wars: Rebellion Rise of the Empire"}',
    'google-news',
    10,
    now()
)

```