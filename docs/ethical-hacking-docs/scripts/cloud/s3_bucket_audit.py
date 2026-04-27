#!/usr/bin/env python3
"""
s3_bucket_audit.py — Owner-side audit of S3 buckets for public exposure.

Iterates over every bucket in your AWS account (via boto3) and checks:

  - Bucket-level Public Access Block configuration
  - Bucket policy (parsed for Principal:"*" and AWS:* with no Condition)
  - Bucket ACL (any 'AllUsers' / 'AuthenticatedUsers' grants)
  - Account-level Public Access Block (warns if disabled)
  - Server-side encryption configuration
  - Versioning + MFA Delete
  - Logging
  - HTTPS-only enforcement (TLS-only via bucket policy condition)
  - Object Ownership (BucketOwnerEnforced disables ACLs entirely - good)

This is read-only. No bucket contents are listed or downloaded.

⚠️ AUTHORIZATION REQUIRED ⚠️
Run only against AWS accounts you own or are authorized to audit.
The IAM identity you use needs s3:GetBucket*, s3:ListAllMyBuckets, and
s3control:GetPublicAccessBlock.

Dependencies:
    pip install boto3

Usage:
    python3 s3_bucket_audit.py --profile audit-readonly
    python3 s3_bucket_audit.py --profile prod --output audit.json
    python3 s3_bucket_audit.py --profile prod --bucket only-this-one
    python3 s3_bucket_audit.py --profile prod --severity high
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field, asdict

try:
    import boto3
    from botocore.exceptions import ClientError, BotoCoreError
except ImportError:
    print("ERROR: boto3 required. pip install boto3", file=sys.stderr)
    sys.exit(2)

PUBLIC_ACL_GROUPS = {
    "http://acs.amazonaws.com/groups/global/AllUsers": "AllUsers (anyone on the internet)",
    "http://acs.amazonaws.com/groups/global/AuthenticatedUsers": "AuthenticatedUsers (any AWS account)",
}


@dataclass
class Finding:
    bucket: str
    severity: str        # info / low / medium / high / critical
    category: str
    detail: str


@dataclass
class BucketReport:
    name: str
    region: str = ""
    public_access_block: dict = field(default_factory=dict)
    bucket_policy: dict | None = None
    bucket_acl_grants: list[dict] = field(default_factory=list)
    encryption: dict | None = None
    versioning: str = ""
    mfa_delete: str = ""
    logging: dict | None = None
    object_ownership: str = ""
    findings: list[Finding] = field(default_factory=list)


def safe(call):
    try:
        return call(), None
    except ClientError as e:
        return None, e.response.get("Error", {}).get("Code", str(e))
    except BotoCoreError as e:
        return None, str(e)


def audit_account_pab(client_s3control, account_id: str) -> dict:
    res, err = safe(lambda: client_s3control.get_public_access_block(AccountId=account_id))
    if err:
        if "NoSuchPublicAccessBlockConfiguration" in str(err):
            return {"BlockPublicAcls": False, "IgnorePublicAcls": False,
                    "BlockPublicPolicy": False, "RestrictPublicBuckets": False,
                    "_note": "No account-level PAB configured"}
        return {"_error": str(err)}
    return res.get("PublicAccessBlockConfiguration", {}) if res else {}


def audit_bucket(s3, bucket: str) -> BucketReport:
    rep = BucketReport(name=bucket)

    # Region
    res, err = safe(lambda: s3.get_bucket_location(Bucket=bucket))
    if res:
        rep.region = res.get("LocationConstraint") or "us-east-1"

    # Public Access Block (bucket-level)
    res, err = safe(lambda: s3.get_public_access_block(Bucket=bucket))
    if res:
        rep.public_access_block = res.get("PublicAccessBlockConfiguration", {})
    elif err and "NoSuchPublicAccessBlockConfiguration" in str(err):
        rep.public_access_block = {"_note": "Not configured"}
        rep.findings.append(Finding(bucket=bucket, severity="medium",
                                    category="public_access_block",
                                    detail="No bucket-level Public Access Block configured."))
    elif err:
        rep.public_access_block = {"_error": str(err)}

    # Bucket policy
    res, err = safe(lambda: s3.get_bucket_policy(Bucket=bucket))
    if res:
        try:
            rep.bucket_policy = json.loads(res.get("Policy", "{}"))
            analyze_policy(bucket, rep)
        except json.JSONDecodeError:
            rep.bucket_policy = {"_raw": res.get("Policy", "")[:500]}
    elif err and "NoSuchBucketPolicy" not in str(err):
        rep.findings.append(Finding(bucket=bucket, severity="info", category="policy",
                                    detail=f"Could not read policy: {err}"))

    # ACL
    res, err = safe(lambda: s3.get_bucket_acl(Bucket=bucket))
    if res:
        for grant in res.get("Grants", []):
            grantee = grant.get("Grantee", {}) or {}
            uri = grantee.get("URI")
            perm = grant.get("Permission", "")
            rep.bucket_acl_grants.append({
                "type": grantee.get("Type"),
                "uri": uri,
                "id": grantee.get("ID"),
                "permission": perm,
            })
            if uri in PUBLIC_ACL_GROUPS:
                sev = "critical" if uri.endswith("AllUsers") else "high"
                rep.findings.append(Finding(
                    bucket=bucket, severity=sev, category="public_acl",
                    detail=f"ACL grants {perm} to {PUBLIC_ACL_GROUPS[uri]}",
                ))

    # Encryption
    res, err = safe(lambda: s3.get_bucket_encryption(Bucket=bucket))
    if res:
        rep.encryption = res.get("ServerSideEncryptionConfiguration", {})
    elif err and "ServerSideEncryptionConfigurationNotFoundError" in str(err):
        rep.encryption = None
        rep.findings.append(Finding(bucket=bucket, severity="medium", category="encryption",
                                    detail="No default encryption configured."))

    # Versioning + MFA Delete
    res, err = safe(lambda: s3.get_bucket_versioning(Bucket=bucket))
    if res:
        rep.versioning = res.get("Status") or "Disabled"
        rep.mfa_delete = res.get("MFADelete") or "Disabled"
        if rep.versioning != "Enabled":
            rep.findings.append(Finding(bucket=bucket, severity="low", category="versioning",
                                        detail="Versioning not enabled — accidental deletion not protected."))

    # Logging
    res, err = safe(lambda: s3.get_bucket_logging(Bucket=bucket))
    if res:
        if not res.get("LoggingEnabled"):
            rep.findings.append(Finding(bucket=bucket, severity="low", category="logging",
                                        detail="Server access logging disabled."))
        else:
            rep.logging = res["LoggingEnabled"]

    # Object ownership
    res, err = safe(lambda: s3.get_bucket_ownership_controls(Bucket=bucket))
    if res:
        rules = res.get("OwnershipControls", {}).get("Rules", [])
        if rules:
            rep.object_ownership = rules[0].get("ObjectOwnership", "")
            if rep.object_ownership != "BucketOwnerEnforced":
                rep.findings.append(Finding(bucket=bucket, severity="low", category="object_ownership",
                                            detail=f"Object Ownership is {rep.object_ownership}; BucketOwnerEnforced disables ACLs entirely (recommended)."))

    # Cross-check PAB
    pab = rep.public_access_block
    if isinstance(pab, dict) and pab.get("_note") != "Not configured" and "_error" not in pab:
        for k in ("BlockPublicAcls", "IgnorePublicAcls", "BlockPublicPolicy", "RestrictPublicBuckets"):
            if pab.get(k) is False:
                rep.findings.append(Finding(
                    bucket=bucket, severity="medium", category="public_access_block",
                    detail=f"PAB setting {k} is False",
                ))

    return rep


def analyze_policy(bucket: str, rep: BucketReport) -> None:
    """Look for Allow + Principal:* with no defensive Condition."""
    if not rep.bucket_policy:
        return
    statements = rep.bucket_policy.get("Statement", [])
    if isinstance(statements, dict):
        statements = [statements]
    https_only = False
    public_seen = False
    for stmt in statements:
        effect = stmt.get("Effect")
        principal = stmt.get("Principal")
        is_public = False
        if isinstance(principal, str) and principal == "*":
            is_public = True
        elif isinstance(principal, dict):
            aws = principal.get("AWS")
            if aws == "*" or (isinstance(aws, list) and "*" in aws):
                is_public = True
            cf = principal.get("CanonicalUser")
            if isinstance(cf, str) and cf == "*":
                is_public = True
        if effect == "Allow" and is_public:
            cond = stmt.get("Condition", {})
            if not cond:
                rep.findings.append(Finding(
                    bucket=bucket, severity="critical", category="public_policy",
                    detail=f"Policy Allow + Principal:* with no Condition. Action: {stmt.get('Action')}",
                ))
                public_seen = True
            else:
                # Has condition — could be SourceVpce, SourceIp, etc. Lower severity.
                rep.findings.append(Finding(
                    bucket=bucket, severity="medium", category="conditional_public",
                    detail=f"Policy Allow + Principal:* with Condition: {list(cond.keys())}",
                ))
        if effect == "Deny" and stmt.get("Condition", {}).get("Bool", {}).get("aws:SecureTransport") in ("false", False):
            https_only = True

    if not https_only:
        rep.findings.append(Finding(
            bucket=bucket, severity="low", category="https_only",
            detail="Bucket policy does not deny non-HTTPS access (aws:SecureTransport=false).",
        ))


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--profile", help="AWS profile name")
    p.add_argument("--bucket", help="Audit only this bucket")
    p.add_argument("--severity", default="info", help="Filter findings >= this severity")
    p.add_argument("-o", "--output", help="Write JSON to file")
    p.add_argument("--summary", action="store_true", help="Human-readable summary")
    args = p.parse_args()

    session = boto3.Session(profile_name=args.profile) if args.profile else boto3.Session()
    s3 = session.client("s3")
    sts = session.client("sts")
    s3c = session.client("s3control")

    try:
        identity = sts.get_caller_identity()
        account_id = identity["Account"]
        print(f"[*] Auditing account {account_id} as {identity['Arn']}", file=sys.stderr)
    except (ClientError, BotoCoreError) as e:
        print(f"[-] Could not get caller identity: {e}", file=sys.stderr)
        return 1

    account_pab = audit_account_pab(s3c, account_id)
    if isinstance(account_pab, dict) and not all(account_pab.get(k, False)
                                                  for k in ("BlockPublicAcls", "IgnorePublicAcls",
                                                            "BlockPublicPolicy", "RestrictPublicBuckets")):
        print(f"[!] Account-level PAB not fully enabled: {account_pab}", file=sys.stderr)

    if args.bucket:
        bucket_names = [args.bucket]
    else:
        try:
            res = s3.list_buckets()
            bucket_names = [b["Name"] for b in res.get("Buckets", [])]
        except ClientError as e:
            print(f"[-] list_buckets failed: {e}", file=sys.stderr)
            return 1

    print(f"[*] {len(bucket_names)} bucket(s) to audit", file=sys.stderr)

    sev_levels = ["info", "low", "medium", "high", "critical"]
    min_idx = sev_levels.index(args.severity) if args.severity in sev_levels else 0

    reports: list[BucketReport] = []
    for b in bucket_names:
        print(f"[*] {b}", file=sys.stderr)
        rep = audit_bucket(s3, b)
        rep.findings = [f for f in rep.findings if sev_levels.index(f.severity) >= min_idx]
        reports.append(rep)

    payload = {
        "account": account_id,
        "account_public_access_block": account_pab,
        "bucket_count": len(reports),
        "total_findings": sum(len(r.findings) for r in reports),
        "buckets": [asdict(r) for r in reports],
    }

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, default=str)
        print(f"[+] Wrote {args.output}", file=sys.stderr)
    elif args.summary:
        print(f"\nAccount {account_id}: {len(reports)} bucket(s), {payload['total_findings']} finding(s)")
        for r in reports:
            if not r.findings:
                continue
            print(f"\n## {r.name} (region={r.region})")
            for f in sorted(r.findings, key=lambda x: -sev_levels.index(x.severity)):
                print(f"  [{f.severity.upper():9}] {f.category:22} {f.detail}")
    else:
        print(json.dumps(payload, indent=2, default=str))

    return 0


if __name__ == "__main__":
    sys.exit(main())
