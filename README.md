# Sherlock

Sherlock is a service developed by OpenNova for detecting coordinated behavior in social networks.

## How it works

Sherlock runs as a Celery worker and is triggered through asynchronous tasks.

When a task is received:

1. Required input files are downloaded from S3.
2. Results are uploaded back to S3.

## Dependencias
- S3
- Rabbit
- Docker

## Running with Docker

Build the image:

```bash
docker build -t sherlock .
```

Run the container:

```bash
docker run sherlock
```

Configuration is provided through environment variables and access to the corresponding S3 buckets.

## Organization

This project is maintained by **OpenNova**.

---

# License
Licensed under LGPL-2.1. See [LICENSE](./LICENSE) and [NOTICE](./NOTICE.md) for details.

