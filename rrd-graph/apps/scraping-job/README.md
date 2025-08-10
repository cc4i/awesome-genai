# xJob

## Description 

Job is running to scrape content from various media platforms, such as Twitter, Google News, Google Search, etc. 



## Deployment
1. Modify **image, project_id, and deployed region** in ./skaffold.yaml
2. Modify **image** in ./resource/scraping-job.yaml
3. Run following CMDs to deploy


```shell
# Add env variables
echo "" >> .env

# Build & deploy
skaffold run
```