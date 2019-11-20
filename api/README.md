# Download Image to S3 Bucket API

- Description: This API takes URL as input to download and store images to S3 bucket
- Language: Python Flask
- Platform: Docker & AWS (ECS, Fargate, Cloudformation, RDS, IAM, VPC and S3)
- Author: Bhargav Amin


## API Usage

### List all the images from S3 bucket

**Defination**

`GET /list`

**Response**

- `200 OK` on success
- `204 No Content` on no files found in S3 bucket
- `403 Forbidden error` on issue with S3 bucket permissions or no bucket found

### Submitting a download request

**Defination**

`POST /`

**Arguments**

- `"url":string` image url

**Request**
Send request as raw json. For eg.

```json
{
	"url": "https://example.com/demo.jpg"
}
```

**Response**

- `200 OK` on success
- `400 BAD REQUEST` on invalid url
- `404 NOT FOUND` on image format matched
- `500 Internal Server Error` on database connection failure

### API home page display README.md

**Defination**

`GET /`

**Response**

- `200 OK` on success

### API health check endpoint

**Defination**

`GET /ping`

**Response**

- `200 OK` on success

---

# Development Setup

Build and test application in docker locally.

## Build docker image locally

For app directory execute following commands:

- To build app: `docker-compose build`
- To run app: `docker-compose up`

Command to list docker images:

`docker images`

Command to run docker image:

`docker run -p 80:80 --name=api -d api_image_to_s3`

Command to login to container:

`docker exec -it <container id> /bin/bash`

Command to view container logs:

`docker container logs <container id>`
