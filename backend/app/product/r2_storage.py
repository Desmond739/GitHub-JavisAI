from __future__ import annotations

import base64
import hashlib
import hmac
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import (
    R2_ACCESS_KEY_ID, R2_ACCOUNT_ID, R2_BUCKET_NAME, R2_ENCRYPTION_KEY,
    R2_SECRET_ACCESS_KEY,
)
from app.product.store import platform_store, utc_now
from app.product.subscription_service import subscription_service


MAX_SINGLE_UPLOAD_BYTES = 50 * 1024 * 1024


class R2Storage:
    def configured(self) -> bool:
        return all((R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY,
                    R2_BUCKET_NAME, R2_ENCRYPTION_KEY))

    def status(self) -> dict[str, object]:
        used = self.used_bytes()
        plan = subscription_service.current_plan()
        return {
            "provider": "cloudflare_r2", "configured": self.configured(),
            "client_side_encryption": "AES-256-GCM", "used_bytes": used,
            "quota_bytes": plan.included_cloud_bytes,
            "single_upload_limit_bytes": MAX_SINGLE_UPLOAD_BYTES,
        }

    @staticmethod
    def _key() -> bytes:
        try:
            key = base64.urlsafe_b64decode(R2_ENCRYPTION_KEY.encode("ascii"))
        except Exception as error:
            raise RuntimeError("R2 encryption key is invalid.") from error
        if len(key) != 32:
            raise RuntimeError("R2 encryption key must decode to exactly 32 bytes.")
        return key

    @staticmethod
    def _object_key(name: str) -> str:
        clean = re.sub(r"[^A-Za-z0-9._/-]+", "_", name.strip()).strip("./")
        if not clean or ".." in clean.split("/") or len(clean) > 240:
            raise ValueError("Object name is invalid.")
        return f"owners/local/{clean}"

    def used_bytes(self) -> int:
        with platform_store.connection() as connection:
            row = connection.execute("SELECT COALESCE(SUM(size_bytes),0) AS total FROM cloud_objects").fetchone()
        return int(row["total"])

    @staticmethod
    def _sign(key: bytes, message: str) -> bytes:
        return hmac.new(key, message.encode("utf-8"), hashlib.sha256).digest()

    def _request(self, method: str, object_key: str, payload: bytes = b"") -> bytes:
        if not self.configured():
            raise RuntimeError("Cloudflare R2 credentials are not configured.")
        now = datetime.now(timezone.utc)
        amz_date = now.strftime("%Y%m%dT%H%M%SZ")
        date_stamp = now.strftime("%Y%m%d")
        host = f"{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
        canonical_uri = "/" + urllib.parse.quote(f"{R2_BUCKET_NAME}/{object_key}", safe="/-_.~")
        payload_hash = hashlib.sha256(payload).hexdigest()
        canonical_headers = f"host:{host}\nx-amz-content-sha256:{payload_hash}\nx-amz-date:{amz_date}\n"
        signed_headers = "host;x-amz-content-sha256;x-amz-date"
        canonical_request = "\n".join((method, canonical_uri, "", canonical_headers, signed_headers, payload_hash))
        scope = f"{date_stamp}/auto/s3/aws4_request"
        string_to_sign = "AWS4-HMAC-SHA256\n" + amz_date + "\n" + scope + "\n" + hashlib.sha256(canonical_request.encode()).hexdigest()
        date_key = self._sign(("AWS4" + R2_SECRET_ACCESS_KEY).encode(), date_stamp)
        region_key = self._sign(date_key, "auto")
        service_key = self._sign(region_key, "s3")
        signing_key = self._sign(service_key, "aws4_request")
        signature = hmac.new(signing_key, string_to_sign.encode(), hashlib.sha256).hexdigest()
        authorization = f"AWS4-HMAC-SHA256 Credential={R2_ACCESS_KEY_ID}/{scope}, SignedHeaders={signed_headers}, Signature={signature}"
        request = urllib.request.Request(
            f"https://{host}{canonical_uri}", method=method,
            data=payload if method in {"PUT", "POST"} else None,
            headers={"Host": host, "X-Amz-Date": amz_date,
                     "X-Amz-Content-Sha256": payload_hash, "Authorization": authorization},
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.read()
        except urllib.error.HTTPError as error:
            error.read()
            raise RuntimeError(f"R2 request failed with status {error.code}.") from error

    def put(self, name: str, data: bytes) -> dict[str, object]:
        if len(data) > MAX_SINGLE_UPLOAD_BYTES:
            raise ValueError("File exceeds the early-access single-upload limit.")
        plan = subscription_service.current_plan()
        if self.used_bytes() + len(data) > plan.included_cloud_bytes:
            raise ValueError("Cloud storage quota would be exceeded.")
        object_key = self._object_key(name)
        nonce = __import__("os").urandom(12)
        encrypted = b"NAYA1" + nonce + AESGCM(self._key()).encrypt(nonce, data, object_key.encode())
        self._request("PUT", object_key, encrypted)
        digest = hashlib.sha256(data).hexdigest()
        with platform_store.connection() as connection:
            connection.execute(
                "INSERT INTO cloud_objects VALUES(?,?,?,?,?) ON CONFLICT(object_key) DO UPDATE SET "
                "size_bytes=excluded.size_bytes,encrypted_size_bytes=excluded.encrypted_size_bytes,"
                "sha256=excluded.sha256,created_at=excluded.created_at",
                (object_key, len(data), len(encrypted), digest, utc_now()),
            )
        return {"object_key": object_key, "size_bytes": len(data), "sha256": digest, "encrypted": True}

    def get(self, name: str) -> bytes:
        object_key = self._object_key(name)
        encrypted = self._request("GET", object_key)
        if not encrypted.startswith(b"NAYA1") or len(encrypted) < 33:
            raise RuntimeError("Cloud object is not a valid Naya encrypted object.")
        nonce, ciphertext = encrypted[5:17], encrypted[17:]
        return AESGCM(self._key()).decrypt(nonce, ciphertext, object_key.encode())


r2_storage = R2Storage()
