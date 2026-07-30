"""
EUDI-Nexus backend regression tests.

Covers Sprint 1-5 endpoints: paper, issuer (SD-JWT VC + one-time nonce),
verifier, mDoc (ISO 18013-5), trust, compliance, country adapters,
well-known discovery.

Env:
  BASE_URL     — from REACT_APP_BACKEND_URL (HTTP entry point)
  ISSUER_URL   — from backend/.env (aud in proof-JWT)
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Any

from pymongo import MongoClient

import pytest
import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://honor-registry-ai.preview.emergentagent.com").rstrip("/")
# ISSUER_URL matches the value in backend/.env (used as `aud` for proof JWTs)
ISSUER_URL = os.environ.get("ISSUER_URL", "https://honor-registry-ai.preview.emergentagent.com")

API = f"{BASE_URL}/api"


# ---------------------------------------------------------------------------
# Helpers — ES256 proof-JWT signing (cryptography)
# ---------------------------------------------------------------------------
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature


def _b64u(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _b64u_json(obj: dict) -> str:
    return _b64u(json.dumps(obj, separators=(",", ":")).encode())


def _make_es256_key() -> tuple[ec.EllipticCurvePrivateKey, dict]:
    sk = ec.generate_private_key(ec.SECP256R1())
    nums = sk.public_key().public_numbers()
    x = nums.x.to_bytes(32, "big")
    y = nums.y.to_bytes(32, "big")
    jwk = {"kty": "EC", "crv": "P-256", "x": _b64u(x), "y": _b64u(y)}
    return sk, jwk


def _sign_proof_jwt(sk: ec.EllipticCurvePrivateKey, jwk: dict, nonce: str, aud: str) -> str:
    header = {"typ": "openid4vci-proof+jwt", "alg": "ES256", "jwk": jwk}
    payload = {"aud": aud, "iat": int(time.time()), "nonce": nonce}
    signing_input = f"{_b64u_json(header)}.{_b64u_json(payload)}".encode()
    der_sig = sk.sign(signing_input, ec.ECDSA(hashes.SHA256()))
    r, s = decode_dss_signature(der_sig)
    raw = r.to_bytes(32, "big") + s.to_bytes(32, "big")
    return f"{signing_input.decode()}.{_b64u(raw)}"


# ---------------------------------------------------------------------------
# Session fixture
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def s() -> requests.Session:
    sess = requests.Session()
    sess.headers.update({"Content-Type": "application/json"})
    return sess


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
class TestHealth:
    def test_health(self, s):
        r = s.get(f"{API}/health", timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "operational"
        assert data["database"] is True


# ---------------------------------------------------------------------------
# Concept Paper
# ---------------------------------------------------------------------------
class TestPaper:
    def test_chapters(self, s):
        r = s.get(f"{API}/paper/chapters", timeout=15)
        assert r.status_code == 200
        chapters = r.json()
        assert isinstance(chapters, list)
        assert len(chapters) >= 5, f"expected >=5 chapters, got {len(chapters)}"
        slugs = {c["slug"] for c in chapters}
        # Slug spelling: architektur (DE)
        assert any("architek" in sl.lower() for sl in slugs)

    def test_chapter_architektur(self, s):
        # Try both possible slugs
        for slug in ("architektur", "architecture"):
            r = s.get(f"{API}/paper/chapters/{slug}", timeout=15)
            if r.status_code == 200:
                body = r.json()
                assert body.get("body")
                return
        pytest.fail("architektur chapter not found under expected slugs")

    def test_search(self, s):
        r = s.get(f"{API}/paper/search", params={"q": "eIDAS"}, timeout=15)
        assert r.status_code == 200
        results = r.json()
        assert isinstance(results, list)
        assert len(results) >= 1, "search for 'eIDAS' returned no results"


# ---------------------------------------------------------------------------
# Issuer — nonce + credential + one-time-use
# ---------------------------------------------------------------------------
class TestIssuer:
    def test_nonce_fresh(self, s):
        r1 = s.post(f"{API}/issuer/nonce", json={}, timeout=15)
        r2 = s.post(f"{API}/issuer/nonce", json={}, timeout=15)
        assert r1.status_code == 200 and r2.status_code == 200
        d1, d2 = r1.json(), r2.json()
        assert d1["c_nonce_expires_in"] == 300
        assert d1["c_nonce"] != d2["c_nonce"]

    def test_credential_unknown_nonce_rejected(self, s, seeded_session):
        sk, jwk = _make_es256_key()
        proof = _sign_proof_jwt(sk, jwk, nonce="bogus-nonce-not-in-db", aud=ISSUER_URL)
        payload = {
            "vct": "eu.europa.ec.eudi.pid.1",
            "subject_claims": {"family_name": "Mustermann", "given_name": "Erika",
                               "birth_date": "1980-01-01", "email": "e@x.eu"},
            "holder_jwk": jwk,
            "proof_jwt": proof,
            "country_code": "EU",
        }
        r = s.post(f"{API}/issuer/credential", json=payload, timeout=20,
                   headers={"Authorization": f"Bearer {seeded_session['token']}"})
        assert r.status_code == 400
        detail = r.json().get("detail", {})
        reasons = detail.get("reasons") if isinstance(detail, dict) else []
        assert any("nonce" in str(x).lower() for x in reasons or []), f"expected nonce reason: {r.text}"

    def test_e2e_issue_and_verify(self, s, seeded_session):
        auth_h = {"Authorization": f"Bearer {seeded_session['token']}"}
        # 1) nonce
        n = s.post(f"{API}/issuer/nonce", json={}, timeout=15).json()["c_nonce"]

        # 2) proof jwt
        sk, jwk = _make_es256_key()
        proof = _sign_proof_jwt(sk, jwk, nonce=n, aud=ISSUER_URL)

        # 3) issue credential
        req = {
            "vct": "eu.europa.ec.eudi.pid.1",
            "subject_claims": {
                "family_name": "Mustermann",
                "given_name": "Erika",
                "birth_date": "1980-01-01",
                "email": "erika@example.eu",
            },
            "holder_jwk": jwk,
            "proof_jwt": proof,
            "country_code": "EU",
        }
        r = s.post(f"{API}/issuer/credential", json=req, timeout=25, headers=auth_h)
        assert r.status_code == 200, f"issue failed: {r.status_code} {r.text}"
        cred = r.json()
        assert cred["disclosures_count"] >= 4
        assert cred["credential"].count("~") >= 4  # 4 disclosures -> tilde delim

        # 4) verify (no audience/nonce -> no KB-JWT required, per review contract)
        pres = cred["credential"]
        vr = s.post(f"{API}/verifier/verify",
                    json={"presentation": pres},
                    timeout=20)
        assert vr.status_code == 200
        vres = vr.json()
        assert vres["valid"] is True, f"verify failed: {vres}"
        disclosed = vres["disclosed_claims"]
        for k in ("family_name", "given_name", "birth_date", "email"):
            assert k in disclosed, f"missing disclosed {k}: {disclosed}"

        # stash for downstream
        pytest.issued_credential = pres

    def test_nonce_one_time_use(self, s, seeded_session):
        auth_h = {"Authorization": f"Bearer {seeded_session['token']}"}
        # Get a nonce, use it once, try again with same nonce
        n = s.post(f"{API}/issuer/nonce", json={}).json()["c_nonce"]
        sk, jwk = _make_es256_key()
        proof = _sign_proof_jwt(sk, jwk, nonce=n, aud=ISSUER_URL)

        req = {
            "vct": "eu.europa.ec.eudi.pid.1",
            "subject_claims": {"family_name": "A", "given_name": "B",
                               "birth_date": "2000-01-01", "email": "a@b.c"},
            "holder_jwk": jwk,
            "proof_jwt": proof,
            "country_code": "EU",
        }
        r1 = s.post(f"{API}/issuer/credential", json=req, timeout=20, headers=auth_h)
        assert r1.status_code == 200

        # Reuse same nonce+proof
        r2 = s.post(f"{API}/issuer/credential", json=req, timeout=20, headers=auth_h)
        assert r2.status_code == 400
        detail = r2.json().get("detail", {})
        reasons = detail.get("reasons", []) if isinstance(detail, dict) else []
        assert any("nonce" in str(x).lower() for x in reasons), f"expected nonce replay reject: {r2.text}"


# ---------------------------------------------------------------------------
# Verifier — mangled presentation
# ---------------------------------------------------------------------------
class TestVerifier:
    def test_mangled_presentation(self, s):
        r = s.post(f"{API}/verifier/verify",
                   json={"presentation": "not.a.jwt~junk~", "audience": ISSUER_URL},
                   timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert data["valid"] is False
        assert len(data["reasons"]) >= 1

    def test_truncated_presentation(self, s):
        r = s.post(f"{API}/verifier/verify",
                   json={"presentation": "abc", "audience": ISSUER_URL},
                   timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert data["valid"] is False


# ---------------------------------------------------------------------------
# Trust — CA chain persistence + LOTL parse
# ---------------------------------------------------------------------------
class TestTrust:
    def test_ca_chain(self, s):
        r = s.get(f"{API}/trust/ca/chain", timeout=15)
        assert r.status_code == 200
        chain = r.json()
        assert len(chain) == 3
        for cert in chain:
            for f in ("fingerprint_sha256", "subject", "issuer", "pem"):
                assert f in cert, f"missing {f} in {cert}"

    def test_ca_chain_persistent(self, s):
        c1 = s.get(f"{API}/trust/ca/chain").json()
        c2 = s.get(f"{API}/trust/ca/chain").json()
        fp1 = [c["fingerprint_sha256"] for c in c1]
        fp2 = [c["fingerprint_sha256"] for c in c2]
        assert fp1 == fp2, "CA fingerprints changed between calls (not persistent!)"

    def test_lotl_parse(self, s):
        minimal_xml = """<?xml version="1.0" encoding="UTF-8"?>
<TrustServiceStatusList xmlns="http://uri.etsi.org/02231/v2#">
  <SchemeInformation>
    <SchemeTerritory>EU</SchemeTerritory>
    <SchemeOperatorName>
      <Name xml:lang="en">EC</Name>
    </SchemeOperatorName>
    <TSLSequenceNumber>42</TSLSequenceNumber>
    <ListIssueDateTime>2025-01-01T00:00:00Z</ListIssueDateTime>
    <NextUpdate><dateTime>2025-06-01T00:00:00Z</dateTime></NextUpdate>
  </SchemeInformation>
</TrustServiceStatusList>"""
        r = s.post(f"{API}/trust/lotl/parse", json={"xml": minimal_xml}, timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["anchor_count"] >= 0
        assert data["territory"] == "EU"
        assert data["sequence_number"] == 42
        assert data["scheme_operator"]


# ---------------------------------------------------------------------------
# mDoc (ISO 18013-5)
# ---------------------------------------------------------------------------
class TestMDoc:
    device_jwk = {"kty": "EC", "crv": "P-256", "x": _b64u(b"\x01" * 32), "y": _b64u(b"\x02" * 32)}

    def test_issue_verify_e2e(self, s):
        sk, jwk = _make_es256_key()
        payload = {
            "doctype": "org.iso.18013.5.1.mDL",
            "namespaces": {
                "org.iso.18013.5.1": {
                    "family_name": "Doe",
                    "given_name": "Jane",
                    "birth_date": "1990-05-15",
                    "issuing_country": "DE",
                }
            },
            "device_public_key": jwk,
            "country_code": "EU",
        }
        r = s.post(f"{API}/mdoc/issue", json=payload, timeout=20)
        assert r.status_code == 200, r.text
        issued = r.json()
        assert issued["digest_count"] == 4
        assert issued["doctype"] == "org.iso.18013.5.1.mDL"
        mdoc_hex = issued["mdoc_hex"]
        assert len(mdoc_hex) > 0 and all(c in "0123456789abcdefABCDEF" for c in mdoc_hex)

        # Verify CBOR structure has tags 18, 24, 0 by byte-scanning the raw CBOR.
        # CBOR tags: 0 -> 0xc0, 18 -> 0xd2, 24 -> 0xd8 0x18 (see RFC 8949).
        raw = bytes.fromhex(mdoc_hex)
        assert b"\xd2" in raw, "CBOR Tag 18 (COSE_Sign1) not present in mDoc bytes"
        assert b"\xd8\x18" in raw, "CBOR Tag 24 (bstr.cbor) not present in mDoc bytes"
        assert b"\xc0" in raw, "CBOR Tag 0 (tdate) not present in mDoc bytes"
        import cbor2  # ensure lib available for parsers
        _ = cbor2.loads(raw)  # sanity: full decode succeeds

        # Verify mDoc
        vr = s.post(f"{API}/mdoc/verify", json={"mdoc_hex": mdoc_hex}, timeout=20)
        assert vr.status_code == 200, vr.text
        vres = vr.json()
        assert vres["valid"] is True, vres
        assert vres["doctype"] == "org.iso.18013.5.1.mDL"
        assert vres["device_key_present"] is True
        assert "org.iso.18013.5.1" in vres["disclosed_namespaces"]

    def test_verify_random_bytes(self, s):
        r = s.post(f"{API}/mdoc/verify", json={"mdoc_hex": "deadbeefcafe1234"}, timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["valid"] is False
        assert len(data["reasons"]) >= 1

    def test_verify_bad_hex(self, s):
        r = s.post(f"{API}/mdoc/verify", json={"mdoc_hex": "not-hex!!"}, timeout=15)
        assert r.status_code == 400

    def test_engagement(self, s):
        r = s.post(f"{API}/mdoc/engagement", json={}, timeout=15)
        assert r.status_code == 200
        eng = r.json()
        assert "engagement_id" in eng and "device_engagement_hex" in eng
        eid = eng["engagement_id"]

        r2 = s.get(f"{API}/mdoc/engagement/{eid}", timeout=15)
        assert r2.status_code == 200
        eng2 = r2.json()
        assert eng2["engagement_id"] == eid
        assert eng2["device_engagement_hex"] == eng["device_engagement_hex"]

    def test_engagement_not_found(self, s):
        r = s.get(f"{API}/mdoc/engagement/does-not-exist-xxx", timeout=15)
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Compliance
# ---------------------------------------------------------------------------
class TestCompliance:
    def test_metrics(self, s):
        r = s.get(f"{API}/compliance/metrics", timeout=15)
        assert r.status_code == 200
        m = r.json()
        for f in ("total_credentials_issued", "total_presentations_verified",
                  "verification_success_rate", "active_loa_high",
                  "active_loa_substantial", "active_loa_low",
                  "downgrade_incidents", "ai_act_transparency_events",
                  "gdpr_erasure_requests"):
            assert f in m, f"missing metric {f}"
            assert isinstance(m[f], (int, float))

    def test_audit_log_hash_chain(self, s):
        r = s.get(f"{API}/compliance/audit-log", timeout=15)
        assert r.status_code == 200
        events = r.json()
        assert isinstance(events, list) and len(events) >= 1
        for ev in events[:5]:
            for f in ("prev_hash", "hash", "signature"):
                assert f in ev, f"missing {f} in audit event"

    def test_audit_verify(self, s):
        r = s.get(f"{API}/compliance/audit-log/verify", timeout=20)
        assert r.status_code == 200
        d = r.json()
        assert d.get("valid") is True
        assert d.get("checked", 0) > 0

    def test_ai_act_transparency(self, s):
        r = s.get(f"{API}/compliance/ai-act/transparency", timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert isinstance(d.get("regulation"), str)
        assert "system_role" in d
        assert "human_oversight_hook" in d
        assert isinstance(d.get("events"), list)

    def test_dsa_pdf(self, s):
        r = s.get(f"{API}/compliance/dsa/report.pdf", timeout=30)
        assert r.status_code == 200
        assert r.headers.get("content-type", "").startswith("application/pdf")
        assert len(r.content) > 500
        assert r.content[:4] == b"%PDF"

    def test_gdpr_erasure_missing_subject(self, s, seeded_session):
        r = s.post(f"{API}/compliance/gdpr/erasure",
                   json={"subject_hash": "TEST_ghost_hash_zzz", "reason": "GDPR Art. 17"},
                   headers={"Authorization": f"Bearer {seeded_session['token']}"},
                   timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert d["deleted"] == 0


# ---------------------------------------------------------------------------
# Country adapters
# ---------------------------------------------------------------------------
class TestCountry:
    def test_list_countries(self, s):
        r = s.get(f"{API}/country/list", timeout=15)
        assert r.status_code == 200
        cs = r.json()
        assert len(cs) >= 11, f"expected >=11 countries, got {len(cs)}"
        by_code = {c["code"]: c for c in cs}
        for code in ("EU", "FR", "IT", "CH", "PT", "SE", "NO", "DK", "IE", "BR", "US"):
            assert by_code[code]["implemented"] is True, f"{code} should be implemented (Sprint 7)"

    def test_get_country_eu(self, s):
        r = s.get(f"{API}/country/EU", timeout=15)
        assert r.status_code == 200
        assert r.json()["code"] == "EU"

    def test_get_country_unknown(self, s):
        r = s.get(f"{API}/country/XX", timeout=15)
        assert r.status_code == 404

    def test_verify_stub_country_pt(self, s):
        # Sprint 7: PT is now real. A malformed sd-jwt should fail with a REAL
        # crypto reason (not the old 'not yet wired' stub message).
        r = s.post(f"{API}/country/verify",
                   json={"country_code": "PT", "presentation": "abc~", "format": "sd-jwt"},
                   timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert d["valid"] is False
        reasons_blob = " ".join(d["reasons"]).lower()
        assert "not yet wired" not in reasons_blob, f"PT still stubbed: {d}"
        # accept any reasonable crypto/parse failure keyword
        assert any(kw in reasons_blob for kw in ("sd-jwt", "signature", "malformed", "parse", "issuer", "jwt", "decode")), \
            f"Expected real crypto reason, got: {d}"

    def test_verify_unknown_country(self, s):
        r = s.post(f"{API}/country/verify",
                   json={"country_code": "ZZ", "presentation": "x", "format": "sd-jwt"},
                   timeout=15)
        assert r.status_code == 404

    def test_verify_eu_with_valid_credential(self, s, seeded_session):
        # Issue a fresh credential then verify via EU adapter
        n = s.post(f"{API}/issuer/nonce", json={}).json()["c_nonce"]
        sk, jwk = _make_es256_key()
        proof = _sign_proof_jwt(sk, jwk, nonce=n, aud=ISSUER_URL)
        national_id_hash = hashlib.sha256(b"EU-E2E-NID-001").hexdigest()
        req = {
            "vct": "eu.europa.ec.eudi.pid.1",
            "subject_claims": {
                "family_name": "X",
                "given_name": "Y",
                "birth_date": "2000-01-01",
                "email": "y@x.eu",
                "national_id_hash": national_id_hash,
            },
            "holder_jwk": jwk,
            "proof_jwt": proof,
            "country_code": "EU",
        }
        cred = s.post(f"{API}/issuer/credential", json=req, timeout=20,
                      headers={"Authorization": f"Bearer {seeded_session['token']}"}).json()["credential"]

        r = s.post(f"{API}/country/verify",
                   json={"country_code": "EU", "presentation": cred, "format": "sd-jwt"},
                   timeout=20)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["valid"] is True, f"EU adapter verify failed: {d}"


# ---------------------------------------------------------------------------
# Hub + Well-known
# ---------------------------------------------------------------------------
class TestHub:
    def test_repos(self, s):
        r = s.get(f"{API}/hub/repos", timeout=15)
        assert r.status_code == 200
        repos = r.json()
        assert len(repos) >= 10
        for rp in repos:
            for f in ("slug", "url", "category", "description", "role"):
                assert f in rp


class TestWellKnown:
    def test_openid_issuer_metadata(self, s):
        r = s.get(f"{API}/.well-known/openid-credential-issuer", timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["credential_issuer"]
        assert d["credential_endpoint"].endswith("/api/issuer/credential")
        assert d["nonce_endpoint"].endswith("/api/issuer/nonce")
        configs = d["credential_configurations_supported"]
        for k in ("eu.europa.ec.eudi.pid.1", "eu.europa.ec.eudi.mdl.1", "eu.europa.ec.eudi.email.1"):
            assert k in configs
        keys = d["jwks"]["keys"]
        assert len(keys) >= 1
        assert keys[0]["kty"] == "EC"
        assert keys[0]["crv"] == "P-256"

    def test_jwks(self, s):
        r = s.get(f"{API}/.well-known/jwks.json", timeout=15)
        assert r.status_code == 200
        keys = r.json()["keys"]
        assert len(keys) >= 1
        assert keys[0]["kty"] == "EC"

    def test_jwks_matches_issuer(self, s):
        j1 = s.get(f"{API}/.well-known/openid-credential-issuer").json()["jwks"]["keys"][0]
        j2 = s.get(f"{API}/.well-known/jwks.json").json()["keys"][0]
        assert j1.get("x") == j2.get("x")
        assert j1.get("y") == j2.get("y")

# ---------------------------------------------------------------------------
# Sprint 7 — country adapter format constraints
# ---------------------------------------------------------------------------
class TestCountrySprint7:
    def test_us_rejects_sd_jwt(self, s):
        r = s.post(f"{API}/country/verify",
                   json={"country_code": "US", "presentation": "abc~", "format": "sd-jwt"},
                   timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["valid"] is False
        assert any("AAMVA mDL requires ISO 18013-5 mdoc" in x for x in d["reasons"]), d

    def test_br_accepts_sd_jwt(self, s):
        r = s.post(f"{API}/country/verify",
                   json={"country_code": "BR", "presentation": "malformed~", "format": "sd-jwt"},
                   timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        # invalid content but the adapter accepted the format (no format-rejection reason)
        blob = " ".join(d["reasons"]).lower()
        assert "cannot verify format" not in blob, d

    def test_br_accepts_mdoc(self, s):
        r = s.post(f"{API}/country/verify",
                   json={"country_code": "BR", "presentation": "deadbeef", "format": "mdoc"},
                   timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        blob = " ".join(d["reasons"]).lower()
        assert "cannot verify format" not in blob, d


# ---------------------------------------------------------------------------
# Sprint 9 — hub_extras (repos/live + postman-collection)
# ---------------------------------------------------------------------------
class TestHubExtras:
    def test_repos_live(self, s):
        r = s.get(f"{API}/hub/repos/live", timeout=30)
        assert r.status_code == 200, r.text
        repos = r.json()
        assert isinstance(repos, list) and len(repos) >= 10
        for rp in repos:
            assert "github" in rp, f"missing github dict: {rp}"
            g = rp["github"]
            # every entry must have a reachable flag; reachable:false is acceptable
            assert "reachable" in g
            if g.get("reachable"):
                for f in ("stars", "forks", "last_commit"):
                    assert f in g, f"missing {f} in {g}"

    def test_postman_collection(self, s):
        r = s.get(f"{API}/hub/postman-collection", timeout=20)
        assert r.status_code == 200, r.text
        coll = r.json()
        assert coll["info"]["name"]
        assert "postman.com" in coll["info"]["schema"]
        assert isinstance(coll["item"], list) and len(coll["item"]) >= 3
        # each group has items
        total = sum(len(g.get("item", [])) for g in coll["item"])
        assert total >= 10, f"postman item count too low: {total}"


# ---------------------------------------------------------------------------
# Auth (Emergent Google Auth) — seeded session via MongoDB (bypasses OAuth)
# ---------------------------------------------------------------------------


def _test_mongo_db():
    url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    name = os.environ.get("DB_NAME", "eudi_nexus")
    return MongoClient(url, serverSelectionTimeoutMS=5000)[name]


def _seed_auth_session(uid: str, token: str, *, name: str = "Tester") -> None:
    now = datetime.now(timezone.utc)
    db = _test_mongo_db()
    db.users.insert_one(
        {
            "user_id": uid,
            "email": f"t.{uid}@e2e.local",
            "name": name,
            "picture": "",
            "created_at": now,
        }
    )
    db.user_sessions.insert_one(
        {
            "user_id": uid,
            "session_token": token,
            "expires_at": now + timedelta(days=7),
            "created_at": now,
        }
    )


def _cleanup_auth_session(uid: str, token: str) -> None:
    db = _test_mongo_db()
    db.user_sessions.delete_one({"session_token": token})
    db.users.delete_one({"user_id": uid})


@pytest.fixture(scope="module")
def seeded_session():
    """Seed a user + session_token in MongoDB (bypasses OAuth)."""
    token = f"test_session_{int(time.time()*1000)}"
    uid = f"test-user-{int(time.time()*1000)}"
    _seed_auth_session(uid, token)
    yield {"token": token, "user_id": uid, "email": f"t.{uid}@e2e.local"}
    _cleanup_auth_session(uid, token)


class TestAuth:
    def test_issuer_credential_requires_auth(self, s):
        r = s.post(f"{API}/issuer/credential", json={}, timeout=15)
        assert r.status_code == 401, r.text

    def test_gdpr_erasure_requires_auth(self, s):
        r = s.post(f"{API}/compliance/gdpr/erasure",
                   json={"subject_hash": "x", "reason": "y"}, timeout=15)
        assert r.status_code == 401, r.text

    def test_me_unauth(self, s):
        r = s.get(f"{API}/auth/me", timeout=15)
        assert r.status_code == 401

    def test_me_with_bearer(self, s, seeded_session):
        r = requests.get(f"{API}/auth/me",
                         headers={"Authorization": f"Bearer {seeded_session['token']}"},
                         timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["user_id"] == seeded_session["user_id"]
        assert d["email"] == seeded_session["email"]

    def test_issue_credential_with_bearer(self, s, seeded_session):
        headers = {"Authorization": f"Bearer {seeded_session['token']}",
                   "Content-Type": "application/json"}
        # fresh nonce
        n = requests.post(f"{API}/issuer/nonce", json={}, headers=headers, timeout=15).json()["c_nonce"]
        sk, jwk = _make_es256_key()
        proof = _sign_proof_jwt(sk, jwk, nonce=n, aud=ISSUER_URL)
        req = {
            "vct": "eu.europa.ec.eudi.pid.1",
            "subject_claims": {"family_name": "Doe", "given_name": "John",
                               "birth_date": "1990-01-01", "email": "d@e.eu"},
            "holder_jwk": jwk,
            "proof_jwt": proof,
            "country_code": "EU",
        }
        r = requests.post(f"{API}/issuer/credential", json=req, headers=headers, timeout=25)
        assert r.status_code == 200, r.text
        assert r.json()["credential"].count("~") >= 4

    def test_logout_deletes_session(self, s):
        # create a fresh throwaway session so we don't break other tests
        token = f"test_session_logout_{int(time.time()*1000)}"
        uid = f"test-user-lo-{int(time.time()*1000)}"
        _seed_auth_session(uid, token, name="X")
        # sanity
        r0 = requests.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {token}"}, timeout=15)
        assert r0.status_code == 200

        # logout via cookie (endpoint reads cookie only)
        r1 = requests.post(f"{API}/auth/logout",
                           cookies={"session_token": token}, timeout=15)
        assert r1.status_code == 200
        # session removed → subsequent /me returns 401
        r2 = requests.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {token}"}, timeout=15)
        assert r2.status_code == 401, r2.text
        _cleanup_auth_session(uid, token)


# ---------------------------------------------------------------------------
# Sprint 8 — LoA downgrade + human oversight
# ---------------------------------------------------------------------------
def _issue_and_verify(s, seeded_session, vct: str, subject: dict):
    """Helper: issue a credential (auth-gated) then verify it publicly."""
    headers = {"Authorization": f"Bearer {seeded_session['token']}",
               "Content-Type": "application/json"}
    n = requests.post(f"{API}/issuer/nonce", json={}, headers=headers, timeout=15).json()["c_nonce"]
    sk, jwk = _make_es256_key()
    proof = _sign_proof_jwt(sk, jwk, nonce=n, aud=ISSUER_URL)
    req = {
        "vct": vct,
        "subject_claims": subject,
        "holder_jwk": jwk,
        "proof_jwt": proof,
        "country_code": "EU",
    }
    r = requests.post(f"{API}/issuer/credential", json=req, headers=headers, timeout=25)
    assert r.status_code == 200, r.text
    pres = r.json()["credential"]
    vr = s.post(f"{API}/verifier/verify", json={"presentation": pres}, timeout=20)
    assert vr.status_code == 200, vr.text
    assert vr.json()["valid"] is True, vr.json()
    return vr.json()


class TestOversight:
    def test_downgrades_endpoint(self, s):
        r = s.get(f"{API}/compliance/oversight/downgrades", timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_downgrade_detected_high_to_substantial(self, s, seeded_session):
        subj = {
            "family_name": f"DowngradeTest{int(time.time())}",
            "given_name": "Alice",
            "birth_date": "1988-08-08",
            "email": "a@d.eu",
        }
        # 1) high LoA presentation
        _issue_and_verify(s, seeded_session, "eu.europa.ec.eudi.pid.1", subj)
        # 2) substantial LoA presentation (email vct) - same subject fingerprint
        _issue_and_verify(s, seeded_session, "eu.europa.ec.eudi.email.1", subj)

        # compute expected fp
        import hashlib
        fp = hashlib.sha256(
            f"{subj['family_name']}|{subj['given_name']}|{subj['birth_date']}".lower().encode()
        ).hexdigest()

        # find the record
        r = s.get(f"{API}/compliance/oversight/downgrades", params={"limit": 100}, timeout=15)
        assert r.status_code == 200
        recs = r.json()
        mine = [x for x in recs if x.get("subject_fp") == fp]
        assert mine, f"no downgrade record for fp={fp} in {len(recs)} records"
        rec = mine[0]
        assert rec["from_loa"] == "high"
        assert rec["to_loa"] == "substantial"
        assert rec["status"] == "pending"
        pytest.downgrade_fp = fp  # stash

    def test_override_accept(self, s, seeded_session):
        fp = getattr(pytest, "downgrade_fp", None)
        if not fp:
            pytest.skip("prior downgrade test didn't produce a fingerprint")
        r = s.post(f"{API}/compliance/oversight/override",
                   json={"subject_fp": fp, "decision": "accept",
                         "reviewer": "reviewer@e2e.local", "note": "ok"},
                   timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["ok"] is True
        assert d["record"]["status"] == "accepted"

    def test_override_unknown_fp(self, s):
        r = s.post(f"{API}/compliance/oversight/override",
                   json={"subject_fp": "no-such-fp-zzz", "decision": "reject",
                         "reviewer": "r@e.local", "note": "n"},
                   timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert d["ok"] is False
        assert "no pending record" in d["reason"].lower()

