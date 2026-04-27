#!/usr/bin/env python3
"""
aws_iam_analyzer.py — Analyze AWS IAM policies for known privilege-escalation paths.

Loads IAM policies from one of:
  1. A live AWS account via boto3 (with --profile / env credentials)
  2. A directory of JSON policy documents
  3. Stdin (a single concatenated policy doc or list of docs)

Cross-references each principal's effective permissions against the
classic IAM-PrivEsc catalog (Rhino Security Labs / Spencer Gietzen),
and reports each discovered escalation path.

This is a **defensive** analysis tool — it does NOT exploit, modify, or
escalate anything. It tells you which paths exist so you can fix them.

⚠️ AUTHORIZATION REQUIRED ⚠️
Reading IAM policies in a live account requires you have rights to do so.
Run only against accounts you own or are authorized to audit.

Dependencies (live mode only):
    pip install boto3

Usage:
    # Live mode — read from current AWS profile/role
    python3 aws_iam_analyzer.py --profile audit-readonly

    # Single user
    python3 aws_iam_analyzer.py --profile audit-readonly --user alice

    # Offline mode — directory of JSON policies
    python3 aws_iam_analyzer.py --policies ./policy-docs/

    # Stdin
    cat policy.json | python3 aws_iam_analyzer.py --stdin
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

# ---- The privesc catalog ----
# Each entry: name -> required_actions (action sets that must ALL be present;
# any one set in the list is enough for the escalation path).
PRIVESC_PATHS: dict[str, dict] = {
    "CreateAccessKey": {
        "description": "Mint long-term access keys for another user",
        "actions": [["iam:CreateAccessKey"]],
        "severity": "critical",
    },
    "UpdateLoginProfile": {
        "description": "Set/reset the console password of another user",
        "actions": [["iam:UpdateLoginProfile"], ["iam:CreateLoginProfile"]],
        "severity": "critical",
    },
    "AttachUserPolicy": {
        "description": "Attach AdministratorAccess to yourself or another user",
        "actions": [
            ["iam:AttachUserPolicy"],
            ["iam:AttachGroupPolicy"],
            ["iam:AttachRolePolicy"],
        ],
        "severity": "critical",
    },
    "PutUserPolicy": {
        "description": "Inline policy attached to user/group/role",
        "actions": [
            ["iam:PutUserPolicy"],
            ["iam:PutGroupPolicy"],
            ["iam:PutRolePolicy"],
        ],
        "severity": "critical",
    },
    "AddUserToGroup": {
        "description": "Add yourself to an admin group",
        "actions": [["iam:AddUserToGroup"]],
        "severity": "critical",
    },
    "PassRole+EC2": {
        "description": "Launch EC2 instance with admin role attached",
        "actions": [["iam:PassRole", "ec2:RunInstances"]],
        "severity": "critical",
    },
    "PassRole+Lambda+InvokeFunction": {
        "description": "Create + invoke Lambda with admin role",
        "actions": [["iam:PassRole", "lambda:CreateFunction", "lambda:InvokeFunction"]],
        "severity": "critical",
    },
    "PassRole+Lambda+CreateEventSource": {
        "description": "Create Lambda + event source to trigger it",
        "actions": [
            ["iam:PassRole", "lambda:CreateFunction", "lambda:CreateEventSourceMapping",
             "dynamodb:CreateTable", "dynamodb:PutItem"],
            ["iam:PassRole", "lambda:CreateFunction", "lambda:CreateEventSourceMapping"],
        ],
        "severity": "high",
    },
    "PassRole+Lambda+UpdateFunctionCode": {
        "description": "Backdoor an existing Lambda that has an admin role",
        "actions": [["lambda:UpdateFunctionCode"]],
        "severity": "high",
    },
    "PassRole+CloudFormation": {
        "description": "Create CloudFormation stack that deploys with admin role",
        "actions": [["iam:PassRole", "cloudformation:CreateStack"]],
        "severity": "critical",
    },
    "PassRole+Glue+DevEndpoint": {
        "description": "Glue dev endpoint with admin role -> SSH in -> AWS CLI",
        "actions": [["iam:PassRole", "glue:CreateDevEndpoint"]],
        "severity": "high",
    },
    "PassRole+Glue+UpdateExistingJob": {
        "description": "Update existing Glue job to run as admin role",
        "actions": [["glue:UpdateJob"]],
        "severity": "high",
    },
    "PassRole+ECS+RegisterTaskDefinition": {
        "description": "ECS task with admin role attached",
        "actions": [["iam:PassRole", "ecs:RegisterTaskDefinition", "ecs:RunTask"]],
        "severity": "critical",
    },
    "PassRole+SageMaker+Notebook": {
        "description": "SageMaker notebook with admin role",
        "actions": [
            ["iam:PassRole", "sagemaker:CreateNotebookInstance",
             "sagemaker:CreatePresignedNotebookInstanceUrl"],
        ],
        "severity": "high",
    },
    "PassRole+DataPipeline": {
        "description": "Create a Data Pipeline with admin role",
        "actions": [["iam:PassRole", "datapipeline:CreatePipeline", "datapipeline:PutPipelineDefinition"]],
        "severity": "high",
    },
    "AssumeRole_via_TrustPolicy": {
        "description": "sts:AssumeRole on a role with overly permissive trust policy",
        "actions": [["sts:AssumeRole"]],
        "severity": "info",   # depends on trust policy
    },
    "UpdateAssumeRolePolicy": {
        "description": "Modify a role's trust policy so YOU can assume it",
        "actions": [["iam:UpdateAssumeRolePolicy", "sts:AssumeRole"]],
        "severity": "critical",
    },
    "iam:PassRole_only": {
        "description": "iam:PassRole alone — combined with any compute service launch is privesc",
        "actions": [["iam:PassRole"]],
        "severity": "high",
    },
    "EditExistingPolicy_CreateVersion": {
        "description": "Edit a policy that's attached to a privileged role",
        "actions": [["iam:CreatePolicyVersion"], ["iam:SetDefaultPolicyVersion"]],
        "severity": "critical",
    },
    "EC2_RebootWithUserData": {
        "description": "Modify EC2 user-data on a stopped instance with priv role",
        "actions": [["ec2:ModifyInstanceAttribute"]],
        "severity": "high",
    },
    "SSM_StartSession": {
        "description": "Session Manager into an instance running as a privileged role",
        "actions": [["ssm:StartSession"]],
        "severity": "high",
    },
    "SSM_SendCommand": {
        "description": "Run command on EC2 via SSM as the instance role",
        "actions": [["ssm:SendCommand"]],
        "severity": "high",
    },
    "S3_BucketPolicy_Wildcard": {
        "description": "Modify any bucket policy you can reach (data-side risk, not IAM)",
        "actions": [["s3:PutBucketPolicy"]],
        "severity": "medium",
    },
}


@dataclass
class Finding:
    principal: str
    principal_type: str          # user / group / role / inline
    path: str                    # PrivescPath name
    description: str
    severity: str
    actions_matched: list[str]
    resource_scope: str          # "*" or actual ARNs


@dataclass
class PrincipalEffective:
    name: str
    type: str
    actions: dict[str, list[str]] = field(default_factory=dict)   # action -> list of resource scopes


# ---- Policy parsing ----

def normalize_actions(action_field) -> list[str]:
    if isinstance(action_field, str):
        return [action_field]
    if isinstance(action_field, list):
        return [a for a in action_field if isinstance(a, str)]
    return []


def normalize_resources(resource_field) -> list[str]:
    if isinstance(resource_field, str):
        return [resource_field]
    if isinstance(resource_field, list):
        return [r for r in resource_field if isinstance(r, str)]
    return ["*"]


def policy_to_actions(policy_doc: dict) -> dict[str, list[str]]:
    """Return {action_pattern: [resource, ...]} for every Allow statement."""
    out: dict[str, list[str]] = {}
    for stmt in policy_doc.get("Statement", []):
        if isinstance(stmt, str):
            continue
        if stmt.get("Effect", "Allow") != "Allow":
            continue
        actions = normalize_actions(stmt.get("Action", [])) + normalize_actions(stmt.get("NotAction", []))
        resources = normalize_resources(stmt.get("Resource", "*"))
        for a in actions:
            out.setdefault(a, []).extend(resources)
    return out


def action_matches(pattern: str, target: str) -> bool:
    """AWS wildcard match. iam:* matches iam:CreateUser, * matches anything."""
    pattern = pattern.lower()
    target = target.lower()
    if pattern == target or pattern == "*":
        return True
    # AWS supports * and ? wildcards in actions
    import fnmatch
    return fnmatch.fnmatchcase(target, pattern)


def has_action(actions: dict[str, list[str]], required: str) -> tuple[bool, list[str]]:
    """Returns (has_it, matched_resources). Matches wildcards."""
    for a, res in actions.items():
        if action_matches(a, required):
            return True, res
    return False, []


def evaluate_principal(principal: PrincipalEffective) -> list[Finding]:
    findings: list[Finding] = []
    for path_name, spec in PRIVESC_PATHS.items():
        # spec["actions"] is a list of action-sets; ANY one fully satisfied = privesc
        for action_set in spec["actions"]:
            matched_actions = []
            matched_resources = set()
            ok = True
            for required in action_set:
                has, res = has_action(principal.actions, required)
                if not has:
                    ok = False
                    break
                matched_actions.append(required)
                matched_resources.update(res)
            if ok:
                findings.append(Finding(
                    principal=principal.name,
                    principal_type=principal.type,
                    path=path_name,
                    description=spec["description"],
                    severity=spec["severity"],
                    actions_matched=matched_actions,
                    resource_scope=", ".join(sorted(matched_resources)) or "*",
                ))
                break    # don't double-report same path
    return findings


# ---- Live mode (boto3) ----

def collect_live(profile: str | None, only_user: str | None) -> list[PrincipalEffective]:
    try:
        import boto3
        from botocore.exceptions import ClientError, BotoCoreError
    except ImportError:
        print("ERROR: boto3 required for live mode. pip install boto3", file=sys.stderr)
        sys.exit(2)

    session = boto3.Session(profile_name=profile) if profile else boto3.Session()
    iam = session.client("iam")
    out: list[PrincipalEffective] = []

    # Users
    paginator = iam.get_paginator("list_users")
    for page in paginator.paginate():
        for user in page["Users"]:
            uname = user["UserName"]
            if only_user and uname != only_user:
                continue
            actions = collect_user_policies(iam, uname)
            out.append(PrincipalEffective(name=uname, type="user", actions=actions))

    if not only_user:
        # Roles
        paginator = iam.get_paginator("list_roles")
        for page in paginator.paginate():
            for role in page["Roles"]:
                rname = role["RoleName"]
                actions = collect_role_policies(iam, rname)
                out.append(PrincipalEffective(name=rname, type="role", actions=actions))

    return out


def collect_user_policies(iam, username: str) -> dict[str, list[str]]:
    actions: dict[str, list[str]] = {}
    # Inline
    for pname in iam.list_user_policies(UserName=username).get("PolicyNames", []):
        doc = iam.get_user_policy(UserName=username, PolicyName=pname).get("PolicyDocument", {})
        for a, r in policy_to_actions(doc).items():
            actions.setdefault(a, []).extend(r)
    # Attached managed
    for ap in iam.list_attached_user_policies(UserName=username).get("AttachedPolicies", []):
        actions = merge_managed(iam, actions, ap["PolicyArn"])
    # Group memberships
    for grp in iam.list_groups_for_user(UserName=username).get("Groups", []):
        gname = grp["GroupName"]
        for pname in iam.list_group_policies(GroupName=gname).get("PolicyNames", []):
            doc = iam.get_group_policy(GroupName=gname, PolicyName=pname).get("PolicyDocument", {})
            for a, r in policy_to_actions(doc).items():
                actions.setdefault(a, []).extend(r)
        for ap in iam.list_attached_group_policies(GroupName=gname).get("AttachedPolicies", []):
            actions = merge_managed(iam, actions, ap["PolicyArn"])
    return actions


def collect_role_policies(iam, rolename: str) -> dict[str, list[str]]:
    actions: dict[str, list[str]] = {}
    for pname in iam.list_role_policies(RoleName=rolename).get("PolicyNames", []):
        doc = iam.get_role_policy(RoleName=rolename, PolicyName=pname).get("PolicyDocument", {})
        for a, r in policy_to_actions(doc).items():
            actions.setdefault(a, []).extend(r)
    for ap in iam.list_attached_role_policies(RoleName=rolename).get("AttachedPolicies", []):
        actions = merge_managed(iam, actions, ap["PolicyArn"])
    return actions


def merge_managed(iam, actions: dict[str, list[str]], policy_arn: str) -> dict[str, list[str]]:
    try:
        meta = iam.get_policy(PolicyArn=policy_arn)["Policy"]
        ver_id = meta["DefaultVersionId"]
        doc = iam.get_policy_version(PolicyArn=policy_arn, VersionId=ver_id)["PolicyVersion"]["Document"]
    except Exception:
        return actions
    for a, r in policy_to_actions(doc).items():
        actions.setdefault(a, []).extend(r)
    return actions


# ---- Offline mode ----

def collect_offline(policy_dir: str) -> list[PrincipalEffective]:
    out: list[PrincipalEffective] = []
    for jf in Path(policy_dir).rglob("*.json"):
        try:
            with open(jf, encoding="utf-8") as f:
                doc = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        # Accept either a raw policy doc or a wrapper
        if "Statement" in doc:
            actions = policy_to_actions(doc)
            out.append(PrincipalEffective(name=jf.stem, type="policy_doc", actions=actions))
        elif isinstance(doc, list):
            for sub in doc:
                if "Statement" in sub:
                    out.append(PrincipalEffective(name=jf.stem, type="policy_doc",
                                                  actions=policy_to_actions(sub)))
    return out


def collect_stdin() -> list[PrincipalEffective]:
    blob = sys.stdin.read()
    try:
        doc = json.loads(blob)
    except json.JSONDecodeError as e:
        print(f"[-] Invalid JSON on stdin: {e}", file=sys.stderr)
        return []
    if isinstance(doc, list):
        return [PrincipalEffective(name=f"stdin#{i}", type="policy_doc", actions=policy_to_actions(d))
                for i, d in enumerate(doc) if "Statement" in d]
    return [PrincipalEffective(name="stdin", type="policy_doc", actions=policy_to_actions(doc))]


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    grp = p.add_mutually_exclusive_group(required=True)
    grp.add_argument("--profile", help="AWS profile name (live mode)")
    grp.add_argument("--policies", help="Directory of JSON policy documents (offline)")
    grp.add_argument("--stdin", action="store_true", help="Read a single policy or list from stdin")
    p.add_argument("--user", help="Live mode: only this username")
    p.add_argument("--severity", default="info",
                   help="Filter findings >= this severity (info/low/medium/high/critical)")
    p.add_argument("--json", action="store_true", help="JSON output")
    p.add_argument("-o", "--output", help="Write JSON to file")
    args = p.parse_args()

    if args.profile:
        principals = collect_live(args.profile, args.user)
    elif args.policies:
        principals = collect_offline(args.policies)
    else:
        principals = collect_stdin()

    if not principals:
        print("[-] No principals collected.", file=sys.stderr)
        return 1

    sev_levels = ["info", "low", "medium", "high", "critical"]
    min_idx = sev_levels.index(args.severity) if args.severity in sev_levels else 0

    all_findings: list[Finding] = []
    for pr in principals:
        for f in evaluate_principal(pr):
            if sev_levels.index(f.severity) >= min_idx:
                all_findings.append(f)

    payload = {
        "principal_count": len(principals),
        "finding_count": len(all_findings),
        "findings_by_severity": {
            sev: sum(1 for f in all_findings if f.severity == sev)
            for sev in sev_levels
        },
        "findings": [asdict(f) for f in all_findings],
    }

    if args.json or args.output:
        out = json.dumps(payload, indent=2, default=str)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(out)
            print(f"[+] Wrote {args.output}", file=sys.stderr)
        else:
            print(out)
    else:
        print(f"\n=== AWS IAM Privesc Analysis ===")
        print(f"Principals analyzed: {len(principals)}")
        print(f"Findings: {len(all_findings)}")
        print(f"  by severity: {payload['findings_by_severity']}")
        for f in sorted(all_findings, key=lambda x: -sev_levels.index(x.severity)):
            print(f"\n  [{f.severity.upper():9}] {f.principal_type}/{f.principal}")
            print(f"     path:        {f.path}")
            print(f"     description: {f.description}")
            print(f"     actions:     {', '.join(f.actions_matched)}")
            print(f"     scope:       {f.resource_scope}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
