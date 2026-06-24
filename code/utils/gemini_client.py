"""
LLM client built on AWS Bedrock (Claude 3.5 models).

Text model:   anthropic.claude-3-5-haiku-20241022-v1:0   (fast, low cost)
Vision model: anthropic.claude-3-5-sonnet-20241022-v2:0  (best multimodal accuracy)

Required env vars:
  AWS_ACCESS_KEY_ID
  AWS_SECRET_ACCESS_KEY
  AWS_REGION            (default: us-east-1)

Override models via:
  BEDROCK_TEXT_MODEL
  BEDROCK_VISION_MODEL
"""

import os
import json
import re
import time
import base64
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

TEXT_MODEL   = os.environ.get("BEDROCK_TEXT_MODEL",   "anthropic.claude-3-5-haiku-20241022-v1:0")
VISION_MODEL = os.environ.get("BEDROCK_VISION_MODEL", "anthropic.claude-3-5-sonnet-20241022-v2:0")
AWS_REGION   = os.environ.get("AWS_REGION", "us-east-1")

INTER_CALL_DELAY = float(os.environ.get("INTER_CALL_DELAY", "0.5"))

_MAX_RETRIES      = 4
_RETRY_BASE_DELAY = 5
_RATE_LIMIT_DELAY = 30

_client = None


def _get_client():
    global _client
    if _client is None:
        key    = os.environ.get("AWS_ACCESS_KEY_ID")
        secret = os.environ.get("AWS_SECRET_ACCESS_KEY")
        if not key or not secret:
            raise EnvironmentError(
                "AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY must be set. "
                "See .env.example for setup instructions."
            )
        _client = boto3.client(
            "bedrock-runtime",
            region_name=AWS_REGION,
            aws_access_key_id=key,
            aws_secret_access_key=secret,
        )
    return _client


def _extract_json(text: str) -> dict:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    fence = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
    if fence:
        try:
            return json.loads(fence.group(1))
        except json.JSONDecodeError:
            pass
    brace = re.search(r"\{[\s\S]+\}", text)
    if brace:
        try:
            return json.loads(brace.group(0))
        except json.JSONDecodeError:
            pass
    raise ValueError(f"Could not extract JSON from response: {text[:300]}")


def _invoke(model_id: str, messages: list) -> str:
    client = _get_client()
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1024,
        "temperature": 0.0,
        "messages": messages,
    })
    for attempt in range(_MAX_RETRIES):
        try:
            time.sleep(INTER_CALL_DELAY)
            response = client.invoke_model(modelId=model_id, body=body)
            result = json.loads(response["body"].read())
            return result["content"][0]["text"]
        except ClientError as e:
            code = e.response["Error"]["Code"]
            if code in ("ThrottlingException", "TooManyRequestsException"):
                wait = _RATE_LIMIT_DELAY * (attempt + 1)
                print(f"  [bedrock] throttled — waiting {wait}s (attempt {attempt+1}/{_MAX_RETRIES})")
            elif attempt < _MAX_RETRIES - 1:
                wait = _RETRY_BASE_DELAY * (2 ** attempt)
                print(f"  [bedrock] retry {attempt+1}/{_MAX_RETRIES} after {wait}s — {code}")
            else:
                raise
            time.sleep(wait)
    raise RuntimeError("Bedrock call failed after all retries.")


def call_text(prompt: str, model=None) -> dict:
    model_id = model or TEXT_MODEL
    messages = [{"role": "user", "content": prompt}]
    text = _invoke(model_id, messages)
    return _extract_json(text)


def call_vision(prompt: str, images: list, model=None) -> dict:
    """images: list of absolute file paths."""
    model_id = model or VISION_MODEL

    content = [{"type": "text", "text": prompt}]
    for img_path in images:
        if isinstance(img_path, str) and os.path.exists(img_path):
            try:
                with open(img_path, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": b64,
                    },
                })
            except Exception as e:
                print(f"  [bedrock-vision] failed to load {img_path}: {e}")
        else:
            print(f"  [bedrock-vision] image not found: {img_path}")

    messages = [{"role": "user", "content": content}]
    text = _invoke(model_id, messages)
    return _extract_json(text)
