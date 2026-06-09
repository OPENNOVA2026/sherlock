import csv
import io
import json
import os
import tempfile
from collections.abc import Iterable
from typing import Any

import boto3
from botocore.exceptions import ClientError
from docx import Document

from src.core.logging import get_logger
from src.core.settings import settings

logger = get_logger(__name__)


class S3Client:
    def __init__(self):
        params = {"endpoint_url": settings.aws_s3_endpoint}
        if aws_access_key_id := settings.aws_access_key:
            params["aws_access_key_id"] = aws_access_key_id
        if aws_secret_access_key := settings.aws_secret_key:
            params["aws_secret_access_key"] = aws_secret_access_key
        if region_name := settings.aws_region:
            params["region_name"] = region_name

        self.s3 = boto3.client("s3", **params)

    def read_twitter_interactions(
        self, topic_id: str, research_id: str
    ) -> Iterable[dict]:
        logger.info("Reading twitter interactions")
        path = f"topic_{topic_id}/research_{research_id}/twitter_interactions.jsonl"
        with tempfile.TemporaryFile(mode="w+b") as tmp_file:
            bucket = settings.aws_s3_input_bucket
            self.s3.download_fileobj(bucket, path, tmp_file)
            tmp_file.seek(0)
            for line in tmp_file:
                yield json.loads(line.decode("utf-8"))

    def read_twitter_posts(self, topic_id: str, research_id: str) -> Iterable[dict]:
        logger.info("Reading twitter posts")
        path = f"topic_{topic_id}/research_{research_id}/twitter_posts.jsonl"
        with tempfile.TemporaryFile(mode="w+b") as tmp_file:
            bucket = settings.aws_s3_input_bucket
            self.s3.download_fileobj(bucket, path, tmp_file)
            tmp_file.seek(0)
            for line in tmp_file:
                yield json.loads(line.decode("utf-8"))

    def post_cib_report(self, doc: Document, topic_id: str, research_id: str):
        path = f"topic_{topic_id}/research_{research_id}/cib_report.docx"
        logger.info(f"Posting CIB report to {path}")

        buf = io.BytesIO()
        doc.save(buf)
        buf.seek(0)

        if settings.local_exec:
            full_path = f"./locals/{path}"
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "wb") as f:
                f.write(buf.getvalue())
            logger.info(f"[LOCAL MODE] CIB report saved to {full_path}")

        else:
            try:
                self.s3.put_object(
                    Bucket=settings.aws_s3_output_bucket,
                    Key=path,
                    Body=buf.getvalue(),
                    ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            except ClientError as e:
                logger.error(f"Failed to upload CIB report to {path}: {e}")
                raise

    def post_cib_graph(self, graph_html: str, topic_id: str, research_id: str):
        path = f"topic_{topic_id}/research_{research_id}/cib_graph.html"
        logger.info(f"Posting CIB graph to {path}")
        if settings.local_exec:
            full_path = f"./locals/{path}"
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(graph_html)
            logger.info(f"[LOCAL MODE] Graph report saved to {full_path}")

        else:
            try:
                self.s3.put_object(
                    Bucket=settings.aws_s3_output_bucket,
                    Key=path,
                    Body=graph_html.encode("utf-8"),
                    ContentType="text/html; charset=utf-8",
                )
            except ClientError as e:
                logger.error(f"Failed to upload Graph report to {path}: {e}")
                raise

    def post_cb_metadata(self, metadata: str, topic_id: str, research_id: str):
        path = f"topic_{topic_id}/research_{research_id}/graph_insights.json"
        logger.info(f"Posting Explainability report to {path}")
        if settings.local_exec:
            full_path = f"./locals/{path}"
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(metadata)
            logger.info(f"[LOCAL MODE] Explainability report saved to {full_path}")

        else:
            try:
                self.s3.put_object(
                    Bucket=settings.aws_s3_output_bucket,
                    Key=path,
                    Body=metadata.encode("utf-8"),
                    ContentType="text/html; charset=utf-8",
                )
            except ClientError as e:
                logger.error(f"Failed to upload Explainability report to {path}: {e}")
                raise

    def post_cb_aggregate(self, aggregated: str, topic_id: str, research_id: str):
        path = f"topic_{topic_id}/research_{research_id}/coordination_aggregate.json"
        logger.info(f"Posting Aggregated report to {path}")
        if settings.local_exec:
            full_path = f"./locals/{path}"
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(aggregated)
            logger.info(f"[LOCAL MODE] Aggregated report saved to {full_path}")

        else:
            try:
                self.s3.put_object(
                    Bucket=settings.aws_s3_output_bucket,
                    Key=path,
                    Body=aggregated.encode("utf-8"),
                    ContentType="text/html; charset=utf-8",
                )
            except ClientError as e:
                logger.error(f"Failed to upload Aggregated report to {path}: {e}")
                raise

    def post_csv(
        self,
        filename: str,
        rows: list[dict[str, Any]],
        fieldnames: list[str],
        topic_id: str,
        research_id: str,
    ) -> str:
        path = f"topic_{topic_id}/research_{research_id}/{filename}"
        logger.info(f"Posting CSV to {path}")

        row_list = list(rows)

        buf = io.StringIO(newline="")
        writer = csv.DictWriter(
            buf,
            fieldnames=list(fieldnames),
            extrasaction="ignore",
            dialect="excel",
        )
        writer.writeheader()
        for r in row_list:
            writer.writerow(dict(r))

        data = buf.getvalue().encode("utf-8")

        if settings.local_exec:
            full_path = f"./locals/{path}"
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "wb") as f:
                f.write(data)
            logger.info(f"[LOCAL MODE] CSV saved to {full_path}")
        else:
            try:
                self.s3.put_object(
                    Bucket=settings.aws_s3_output_bucket,
                    Key=path,
                    Body=data,
                    ContentType="text/csv; charset=utf-8",
                )
            except ClientError as e:
                logger.error(f"Failed to upload CSV to {path}: {e}")
                raise

        return path
