#!/usr/bin/env bash
# File UUID: 2f6a9d13-8c47-4e05-b1d3-7a5e0c9f4b28
# EXPERIMENTAL CODE. Do not use in production.
# Builds the portable CloudFormation template + Lambda zip and uploads both to a
# public-read S3 bucket you own, then prints the one-click Launch Stack URL.
# Lambda reads code from a bucket in the same region, so run once per region.
#   scripts/publish_oneclick.sh <bucket> [profile] [region]
set -euo pipefail
BUCKET=${1:?usage: publish_oneclick.sh <bucket> [profile] [region]}
PROFILE=${2:-default}; REGION=${3:-us-east-1}
VERSION=$(git rev-parse --short HEAD)
KEY="heyhuman/${VERSION}/lambda.zip"; TKEY="heyhuman/${VERSION}/heyhuman.template.json"
OUT=$(mktemp -d)
(cd lambda && zip -qr "$OUT/lambda.zip" . -x '__pycache__/*' '*.pyc')
(cd infra/cdk && npx --yes aws-cdk@2 synth -q -c oneclick=true -c codeBucket="$BUCKET" -c codeKey="$KEY" \
  -o "$OUT/cdk.out" > /dev/null)
cp "$OUT/cdk.out/HeyHumanExperimental.template.json" "$OUT/heyhuman.template.json"
aws s3 cp "$OUT/lambda.zip" "s3://$BUCKET/$KEY" --profile "$PROFILE" --region "$REGION"
aws s3 cp "$OUT/heyhuman.template.json" "s3://$BUCKET/$TKEY" --profile "$PROFILE" --region "$REGION"
aws s3 cp "$OUT/heyhuman.template.json" "s3://$BUCKET/heyhuman/latest/heyhuman.template.json" --profile "$PROFILE" --region "$REGION"
URL="https://${BUCKET}.s3.${REGION}.amazonaws.com/heyhuman/latest/heyhuman.template.json"
echo "Launch Stack URL:"
echo "https://console.aws.amazon.com/cloudformation/home?region=${REGION}#/stacks/quickcreate?templateURL=${URL}&stackName=heyhuman"
