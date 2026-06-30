#!/usr/bin/env python3
"""DTL v0.5 JSON Schema validation harness.

Validates the standalone normative schema shipped in this repo
(schema/relationship.schema.json, Draft 2020-12) against:
  * worked positives  — the three Appendix B examples (B.1/B.2/B.3) + one
                         record for each remaining lifecycle state, and
  * negatives          — required-field / field-constraint / additionalProperties
                         checks, plus the SF5 per-status EXACT proof-set
                         enforcement (the allOf if/then + not:{anyOf:[...]} branches).

28 cases total; every case asserts the schema BEHAVES as designed
(positives validate, negatives fail).

Requires `jsonschema`.  Run:  python3 dtl_validate.py
"""
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

SCHEMA_PATH = Path(__file__).resolve().parent / "schema" / "relationship.schema.json"

schema = json.loads(SCHEMA_PATH.read_text())
Draft202012Validator.check_schema(schema)  # the schema itself must be a valid dialect doc
validator = Draft202012Validator(schema)


def valid(instance):
    return next(iter(validator.iter_errors(instance)), None) is None


# ---- proof-body helpers (internals are profile-defined; any object is fine) ----
def attested(ctrl, at="2026-06-18T10:00:00Z"):
    return {"controller": ctrl, "attested_by": "svc.example", "method": "siwe", "at": at}


def signed(ctrl):
    return {"controller": ctrl, "verificationMethod": ctrl + "#key-1", "signature": "z3Jx"}


# A known-good base record (established / attested) reused for several negatives.
def base():
    return {
        "source": "11155111:123",
        "target": "11155111:456",
        "type": "delegates_to",
        "status": "established",
        "profile": "attested",
        "proofs": {"proposal": attested("0xA11ce"), "confirmation": attested("0xB0b")},
    }


# (name, instance, expected_valid)
cases = []

# ============================ POSITIVES (6) ============================
cases.append((
    "P1  B.1 established / attested {proposal,confirmation}",
    {
        "id": "rel:8004:42",
        "source": "11155111:123", "target": "11155111:456",
        "type": "delegates_to", "status": "established", "profile": "attested",
        "proofs": {"proposal": attested("0xA11ce"), "confirmation": attested("0xB0b", "2026-06-18T10:05:00Z")},
        "created_at": "2026-06-18T10:00:00Z", "updated_at": "2026-06-18T10:05:00Z",
    }, True))

cases.append((
    "P2  B.2 established / signed (each agent its own controller)",
    {
        "id": "rel:example:2",
        "source": "did:web:alpha.example", "target": "did:web:beta.example",
        "type": "depends_on", "status": "established", "profile": "signed",
        "proofs": {"proposal": signed("did:web:alpha.example"), "confirmation": signed("did:web:beta.example")},
    }, True))

cases.append((
    "P3  B.3 revoked / attested {proposal,confirmation,revocation}",
    {
        "id": "rel:8004:42",
        "source": "11155111:123", "target": "11155111:456",
        "type": "delegates_to", "status": "revoked", "profile": "attested",
        "proofs": {
            "proposal": attested("0xA11ce"),
            "confirmation": attested("0xB0b", "2026-06-18T10:05:00Z"),
            "revocation": attested("0xB0b", "2026-06-19T09:00:00Z"),
        },
        "created_at": "2026-06-18T10:00:00Z", "updated_at": "2026-06-19T09:00:00Z",
    }, True))

cases.append((
    "P4  proposed / minimal {proposal}",
    {
        "source": "11155111:1", "target": "11155111:2",
        "type": "can_send_message_to", "status": "proposed", "profile": "attested",
        "proofs": {"proposal": attested("0xA11ce")},
    }, True))

cases.append((
    "P5  declined {proposal,decline}",
    {
        "source": "11155111:1", "target": "11155111:2",
        "type": "depends_on", "status": "declined", "profile": "attested",
        "proofs": {"proposal": attested("0xA11ce"), "decline": attested("0xB0b")},
    }, True))

cases.append((
    "P6  withdrawn {proposal,withdrawal}",
    {
        "source": "11155111:1", "target": "11155111:2",
        "type": "depends_on", "status": "withdrawn", "profile": "attested",
        "proofs": {"proposal": attested("0xA11ce"), "withdrawal": attested("0xA11ce")},
    }, True))

# ===================== NEGATIVES — required fields (6) =====================
for field in ("source", "target", "type", "status", "profile", "proofs"):
    rec = base()
    del rec[field]
    cases.append((f"N  missing required '{field}'", rec, False))

# ================== NEGATIVES — field constraints (4) ==================
r = base(); r["source"] = ""
cases.append(("N  source = ''  (minLength:1)", r, False))
r = base(); r["target"] = ""
cases.append(("N  target = ''  (minLength:1)", r, False))
r = base(); r["status"] = "active"
cases.append(("N  status not in enum ('active')", r, False))
r = base(); r["foo"] = "bar"
cases.append(("N  unknown top-level key (additionalProperties:false)", r, False))

# ============ NEGATIVE — proofs object is sealed (1) ============
r = base(); r["proofs"]["bogus"] = {}
cases.append(("N  unknown key inside proofs (additionalProperties:false)", r, False))

# ===== NEGATIVES — SF5 per-status EXACT proof-set enforcement (11) =====
# proposed must carry ONLY {proposal}
r = base(); r["status"] = "proposed"; r["proofs"] = {"proposal": attested("0xA11ce"), "confirmation": attested("0xB0b")}
cases.append(("N  proposed + confirmation (not:anyOf)", r, False))
r = base(); r["status"] = "proposed"; r["proofs"] = {"proposal": attested("0xA11ce"), "revocation": attested("0xB0b")}
cases.append(("N  proposed + revocation (not:anyOf)", r, False))
r = base(); r["status"] = "proposed"; r["proofs"] = {}
cases.append(("N  proposed with empty proofs (proposal required)", r, False))

# established must carry EXACTLY {proposal,confirmation}
r = base(); r["proofs"]["decline"] = attested("0xB0b")
cases.append(("N  established + decline (not:anyOf)", r, False))
r = base(); r["proofs"] = {"proposal": attested("0xA11ce")}
cases.append(("N  established missing confirmation", r, False))

# declined must carry EXACTLY {proposal,decline}
r = base(); r["status"] = "declined"; r["proofs"] = {"proposal": attested("0xA11ce"), "decline": attested("0xB0b"), "confirmation": attested("0xB0b")}
cases.append(("N  declined + confirmation (not:anyOf)", r, False))
r = base(); r["status"] = "declined"; r["proofs"] = {"proposal": attested("0xA11ce")}
cases.append(("N  declined missing decline", r, False))

# withdrawn must carry EXACTLY {proposal,withdrawal}
r = base(); r["status"] = "withdrawn"; r["proofs"] = {"proposal": attested("0xA11ce"), "withdrawal": attested("0xA11ce"), "confirmation": attested("0xB0b")}
cases.append(("N  withdrawn + confirmation (not:anyOf)", r, False))
r = base(); r["status"] = "withdrawn"; r["proofs"] = {"proposal": attested("0xA11ce")}
cases.append(("N  withdrawn missing withdrawal", r, False))

# revoked must carry EXACTLY {proposal,confirmation,revocation}
r = base(); r["status"] = "revoked"; r["proofs"] = {"proposal": attested("0xA11ce"), "confirmation": attested("0xB0b")}
cases.append(("N  revoked missing revocation", r, False))
r = base(); r["status"] = "revoked"; r["proofs"] = {"proposal": attested("0xA11ce"), "confirmation": attested("0xB0b"), "revocation": attested("0xB0b"), "withdrawal": attested("0xA11ce")}
cases.append(("N  revoked + withdrawal (not:anyOf)", r, False))

# ============================== RUN ==============================
passed = 0
failed = 0
print(f"schema: {SCHEMA_PATH}")
print(f"$id:    {schema.get('$id')}")
print(f"$schema:{schema.get('$schema')}")
print("-" * 72)
for name, instance, expected in cases:
    got = valid(instance)
    ok = (got == expected)
    tag = "VALID  " if got else "INVALID"
    verdict = "ok" if ok else "XX  MISMATCH"
    print(f"[{verdict:>11}] expect {'VALID  ' if expected else 'INVALID'} -> got {tag} | {name}")
    if ok:
        passed += 1
    else:
        failed += 1

print("-" * 72)
print(f"{passed}/{len(cases)} behaved as expected" + ("" if failed == 0 else f"  ({failed} MISMATCH)"))
sys.exit(0 if failed == 0 else 1)
