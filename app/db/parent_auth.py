from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import os

from ._util import _parse_iso_utc
from .connection import managed_connection

PIN_MIN_LENGTH = 4
PIN_MAX_LENGTH = 12
PIN_HASH_ITERATIONS = 200_000
PIN_LOCK_MAX_ATTEMPTS = 5
PIN_LOCK_MINUTES = 15

def parent_pin_configured() -> bool:
    with managed_connection() as conn:
        row = conn.execute("SELECT profile_id FROM parent_auth LIMIT 1").fetchone()
    return row is not None


def parent_pin_locked(now_iso_text: str | None = None) -> tuple[bool, str | None]:
    now = _parse_iso_utc(now_iso_text) if now_iso_text else datetime.now(timezone.utc)
    if now is None:
        now = datetime.now(timezone.utc)
    with managed_connection() as conn:
        row = conn.execute(
            "SELECT locked_until FROM parent_auth LIMIT 1",
        ).fetchone()
    if row is None or row["locked_until"] is None:
        return False, None
    locked_until = _parse_iso_utc(str(row["locked_until"]))
    if locked_until is None or locked_until <= now:
        return False, None
    return True, locked_until.isoformat()


def set_parent_pin(profile_id: int, pin: str, updated_at: str) -> None:
    cleaned = pin.strip()
    if not cleaned.isdigit() or not (PIN_MIN_LENGTH <= len(cleaned) <= PIN_MAX_LENGTH):
        raise ValueError(f"PIN must be {PIN_MIN_LENGTH}-{PIN_MAX_LENGTH} digits.")
    with managed_connection() as conn:
        row = conn.execute(
            "SELECT role FROM profiles WHERE id = ?",
            (int(profile_id),),
        ).fetchone()
        if row is None:
            raise ValueError("Profile not found.")
        if str(row["role"]) != "parent":
            raise ValueError("Only a parent profile can own the parent PIN.")

        conn.execute("DELETE FROM parent_auth")
        pin_salt = os.urandom(16).hex()
        pin_hash = _hash_pin(cleaned, pin_salt)
        conn.execute(
            """
            INSERT INTO parent_auth (profile_id, pin_hash, pin_salt, failed_attempts, locked_until, updated_at)
            VALUES (?, ?, ?, 0, NULL, ?)
            """,
            (int(profile_id), pin_hash, pin_salt, updated_at),
        )


def verify_parent_pin(pin: str, now_iso_text: str | None = None) -> bool:
    now = _parse_iso_utc(now_iso_text) if now_iso_text else datetime.now(timezone.utc)
    if now is None:
        now = datetime.now(timezone.utc)
    with managed_connection() as conn:
        row = conn.execute(
            "SELECT profile_id, pin_hash, pin_salt, locked_until FROM parent_auth LIMIT 1",
        ).fetchone()
    if row is None:
        return False
    if row["locked_until"]:
        locked_until = _parse_iso_utc(str(row["locked_until"]))
        if locked_until is not None and locked_until > now:
            return False
    computed = _hash_pin(pin.strip(), str(row["pin_salt"]))
    return hmac.compare_digest(computed, str(row["pin_hash"]))


def record_parent_auth_failure(now_iso_text: str) -> str | None:
    now = _parse_iso_utc(now_iso_text)
    if now is None:
        now = datetime.now(timezone.utc)
    with managed_connection() as conn:
        row = conn.execute(
            "SELECT profile_id, failed_attempts FROM parent_auth LIMIT 1",
        ).fetchone()
        if row is None:
            return None
        failures = int(row["failed_attempts"]) + 1
        locked_until = None
        if failures >= PIN_LOCK_MAX_ATTEMPTS:
            failures = 0
            locked_until = (now + timedelta(minutes=PIN_LOCK_MINUTES)).isoformat()
        conn.execute(
            """
            UPDATE parent_auth
            SET failed_attempts = ?, locked_until = ?, updated_at = ?
            WHERE profile_id = ?
            """,
            (failures, locked_until, now.isoformat(), int(row["profile_id"])),
        )
    return locked_until


def clear_parent_lock(now_iso_text: str | None = None) -> None:
    updated_at = now_iso_text or datetime.now(timezone.utc).isoformat()
    with managed_connection() as conn:
        conn.execute(
            """
            UPDATE parent_auth
            SET failed_attempts = 0, locked_until = NULL, updated_at = ?
            """,
            (updated_at,),
        )

def _hash_pin(pin: str, salt_hex: str) -> str:
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        pin.encode("utf-8"),
        bytes.fromhex(salt_hex),
        PIN_HASH_ITERATIONS,
    )
    return digest.hex()

