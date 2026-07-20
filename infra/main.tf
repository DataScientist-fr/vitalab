resource "aws_s3_bucket" "vitalab_data" {
  bucket = "vitalab-data"
}

resource "aws_s3_bucket_public_access_block" "vitalab_data" {
  bucket                  = aws_s3_bucket.vitalab_data.id
  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}
