import boto3
from botocore.client import Config

# Setup your R2 credentials here
R2_ACCESS_KEY = "253437c70da9dfbc4b4336cac1ccadf3"
R2_SECRET_KEY = "d3717ca8a3da22fb0bcdddd7a6875ead2b8ce90683f799255daeaf76d60ba61f"
R2_ENDPOINT = "https://42efb1a5802f2665bdd075a9644f6579.r2.cloudflarestorage.com"
R2_PUBLIC_ENDPOINT = "https://pub-a745658fa84043a099e32232cbaa1e6a.r2.dev"
R2_BUCKET = "movie-files"

# S3-compatible R2 client
r2 = boto3.client(
    "s3",
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_ACCESS_KEY,
    aws_secret_access_key=R2_SECRET_KEY,
    region_name="auto",
    config=Config(signature_version="s3v4")
)