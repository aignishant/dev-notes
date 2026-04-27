# Module 6 — Cloud Foundations (AWS, GCP, Azure for ML)

> **Bible Module 6 of 14.** Self-contained. Written for AWS, GCP, and Azure as of 2026. Code samples primarily use **`boto3`** for AWS, **`google-cloud-*`** for GCP, **`azure-*`** for Azure. Concepts apply across clouds; we mark differences when they matter. Assumes Modules 1–5.

---

## 0. Goal, reader, and how to use this module

**Goal.** After this module you can: pick the right compute target for an ML/LLM workload (VM, container, serverless, Kubernetes); write IAM policies that follow least-privilege without breaking your service; store data and model artifacts safely in object storage; manage secrets without hardcoding them; monitor a service end-to-end (logs, metrics, traces, alerts); estimate and control cloud spend; and deploy a containerized FastAPI service end-to-end on at least one cloud.

**Target reader.** Modules 1–4 done (Python, FastAPI). Module 5 (BigQuery) is helpful but not required. No prior cloud experience needed.

**How to use it.** Same as before. Do all 36 problems before reading the solutions.

**Prerequisites.** Modules 1, 4. Helpful: 3, 5.
**Next steps.** Module 7 (Classical ML — first time we deploy a model on this stack), Module 12 (MLOps), Module 13 (LLMOps).

---

## 1. The three clouds — pick one mental model

You will work with at least one of AWS, GCP, or Azure. Often more than one. The good news: 90% of concepts are the same; the names differ. Once you've internalized one cloud's mental model, the others are translation work.

| Concept | AWS | GCP | Azure |
|---|---|---|---|
| Account / project | AWS Account | GCP Project | Azure Subscription |
| Identity / role | IAM Role | Service Account | Managed Identity |
| Object storage | S3 | Cloud Storage (GCS) | Blob Storage |
| VM | EC2 | Compute Engine | Virtual Machine |
| Container service (managed) | ECS / Fargate | Cloud Run | Container Apps |
| Kubernetes (managed) | EKS | GKE | AKS |
| Serverless function | Lambda | Cloud Functions | Functions |
| Secret store | Secrets Manager / Param Store | Secret Manager | Key Vault |
| Logs | CloudWatch Logs | Cloud Logging | Monitor Logs |
| Metrics | CloudWatch Metrics | Cloud Monitoring | Monitor Metrics |
| Managed SQL (Postgres) | RDS | Cloud SQL | Azure DB for PostgreSQL |
| Warehouse | Redshift | BigQuery | Synapse |
| ML platform | SageMaker | Vertex AI | Azure ML |
| Message queue | SQS | Pub/Sub | Service Bus |
| CDN | CloudFront | Cloud CDN | Front Door / CDN |
| DNS | Route 53 | Cloud DNS | Azure DNS |
| IaC native | CloudFormation | Deployment Manager | ARM / Bicep |
| IaC universal | Terraform / Pulumi | Terraform / Pulumi | Terraform / Pulumi |

**Use AWS** if you want the largest service catalog and ecosystem. **Use GCP** if you're heavy on data/ML or BigQuery-first. **Use Azure** if you're enterprise-Microsoft (AD, Office, .NET) or need OpenAI Service. We'll lean toward AWS examples in this module because it's the most ubiquitous, but every section has GCP/Azure callouts.

### 1.1 The IaC reality check

In production, you don't click around the console. You define infrastructure in code with **Terraform** (or Pulumi). Every cloud has a native IaC option (CloudFormation, Bicep, Deployment Manager) but **Terraform** is the cross-cloud standard. Pick it as your default.

```hcl
# main.tf — minimal AWS S3 bucket
resource "aws_s3_bucket" "models" {
  bucket = "myorg-models"
}

resource "aws_s3_bucket_versioning" "models" {
  bucket = aws_s3_bucket.models.id
  versioning_configuration { status = "Enabled" }
}
```

```bash
terraform init
terraform plan -out tf.plan
terraform apply tf.plan
```

This module won't make you a Terraform expert (that's its own book) but every example below has a corresponding `terraform apply`-able resource. Learn the patterns from the SDKs, then encode them in IaC for production.

---

## 2. Identity and access — IAM done right

**The single most important security concept in cloud.** Get IAM wrong → public data leaks, billions in surprise GPU bills, or compromised production. Get it right → you can sleep.

### 2.1 The mental model

There are three kinds of identities:

1. **Human identity** (user) — for engineers, via SSO. Should never have static keys.
2. **Workload identity** — for code running on cloud (EC2, Lambda, Cloud Run, K8s pod). Gets temporary credentials automatically. **Never has hardcoded keys.**
3. **External identity** — for code running outside the cloud (your laptop, GitHub Actions, on-prem). Federated via OIDC where possible; static keys only as last resort.

The IAM model in every cloud is essentially: **identity → role → policy → resource.**

```
[user/workload]  ──── assumes ────►  [role]
                                        │
                                        │ has
                                        ▼
                                    [policy]  ─── grants ──►  actions on  resources
```

### 2.2 The least-privilege principle (and how to actually achieve it)

Two real-world patterns most teams miss:

**Pattern 1: Start broad, narrow with logs.** Give a workload `*` access in dev → look at what it actually uses (CloudTrail / Audit Logs / Activity Log) for a week → write a policy with exactly those actions and resources. Tools: AWS IAM Access Analyzer, GCP Recommender (over-permissioned roles), Azure Privileged Identity Management.

**Pattern 2: Read-only by default, write through specific resources.** Most code reads a lot; writes only a few specific resources. Grant broad read; constrain writes by resource ARN/path.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {"Effect":"Allow","Action":"s3:Get*","Resource":"*"},
    {"Effect":"Allow","Action":"s3:PutObject",
     "Resource":"arn:aws:s3:::myorg-uploads/*"},
    {"Effect":"Allow","Action":"s3:DeleteObject",
     "Resource":"arn:aws:s3:::myorg-uploads/*"}
  ]
}
```

### 2.3 Workload identity — the security default

**Never put static API keys in your code.** Cloud-native deployments get credentials automatically:

- **AWS EC2** — instance profile (IAM role attached to the instance).
- **AWS Lambda** — execution role.
- **AWS Fargate / ECS** — task role.
- **AWS EKS pods** — IAM Roles for Service Accounts (IRSA) via OIDC.
- **GCP Compute / GKE / Cloud Run** — service account attached, accessible via metadata server.
- **Azure VMs / AKS** — Managed Identity / Workload Identity.

Code accesses credentials via the SDK's default chain — no setup needed:

```python
import boto3
s3 = boto3.client("s3")            # auto-discovers credentials from env/instance/role chain
s3.list_objects_v2(Bucket="my-bucket")
```

The same pattern in GCP and Azure:

```python
# GCP
from google.cloud import storage
client = storage.Client()           # ADC: env -> service account file -> metadata server

# Azure
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
cred = DefaultAzureCredential()      # CLI -> Managed Identity -> env -> ...
client = BlobServiceClient(account_url="https://mystg.blob.core.windows.net", credential=cred)
```

### 2.4 GitHub Actions → cloud — federated identity, not static keys

**Don't** copy long-lived AWS access keys into GitHub Secrets. Use OIDC federation:

```yaml
# .github/workflows/deploy.yml
permissions:
  id-token: write       # required to fetch OIDC token
  contents: read

steps:
  - uses: actions/checkout@v4
  - uses: aws-actions/configure-aws-credentials@v4
    with:
      role-to-assume: arn:aws:iam::123456789012:role/github-actions
      aws-region: us-east-1
  - run: aws s3 ls s3://my-bucket
```

Pre-set up an IAM role with a trust policy allowing GitHub's OIDC provider. Now CI gets short-lived credentials per run; no static keys; revoking is instant.

GCP equivalent: **Workload Identity Federation**. Azure: **Managed Identity / OIDC** for pipelines.

### 2.5 Service-control rails (the "do this once" advice)

- **MFA on root + console users.** Non-negotiable.
- **Separate accounts/projects/subscriptions per environment.** dev / staging / prod each isolated. Blast radius limit.
- **Block public S3/GCS access at the org level.** Then opt in per bucket. The big leaks happen because public was the default.
- **CloudTrail / Audit Logs / Activity Log to a centralized logging account** with retention you control (so an attacker can't delete the trail).
- **AWS Organizations / GCP Org Policies / Azure Management Groups** to enforce policies across all accounts (e.g., "no instance can be public IP").

---

## 3. Networking 101 — the bare minimum

Most ML/LLM engineers don't write firewall rules every day, but you'll meet networking when something doesn't work. Here's the survival kit.

### 3.1 VPC — your private network

A **VPC** (Virtual Private Cloud) is a private IP address space in the cloud. You divide it into **subnets** (smaller IP ranges, each tied to one availability zone). Resources go in subnets.

```
VPC: 10.0.0.0/16          (one VPC per project — usually)
├── Public subnet  10.0.1.0/24    (has route to internet gateway)
├── Public subnet  10.0.2.0/24
├── Private subnet 10.0.3.0/24    (no direct internet; uses NAT for egress)
└── Private subnet 10.0.4.0/24
```

**Rule of thumb:** put load balancers and bastion hosts in **public** subnets; put your app, DB, ML services in **private** subnets. Traffic flows: internet → load balancer (public) → app (private) → DB (private).

GCP and Azure have nearly identical concepts: GCP VPC + subnets per region, Azure VNet + subnets.

### 3.2 Security groups vs network ACLs

- **Security Group** (AWS) / **Firewall Rule** (GCP) / **NSG** (Azure) — stateful, attached to a resource (instance, ENI). Deny-by-default. Most teams only use these.
- **Network ACL** — stateless, attached to a subnet. Used for coarse-grained rules at the subnet boundary. Less common.

Stateful means: "if I let TCP/443 in, the response packet on the ephemeral return port is automatically allowed." Stateless means: you'd have to allow both directions.

```
SG_lb: allow 80, 443 from 0.0.0.0/0
SG_app: allow 8080 from SG_lb only
SG_db: allow 5432 from SG_app only
```

**Rule:** allow-list source by *security group reference*, not IP range. As IPs change, the rule still works.

### 3.3 Public vs private endpoints

By default, calling AWS S3 from your VPC goes out the internet (NAT) and back to S3's public endpoint. **Wrong on every count:** costs egress \$, slower, broader attack surface.

Solution: **VPC Endpoint** (AWS) / **Private Service Connect** (GCP) / **Private Endpoint** (Azure). Traffic never leaves the cloud's backbone.

```hcl
# AWS: VPC endpoint for S3 (free)
resource "aws_vpc_endpoint" "s3" {
  vpc_id       = aws_vpc.main.id
  service_name = "com.amazonaws.us-east-1.s3"
}
```

**Real-world.** Without endpoints, NAT gateway charges add up surprisingly fast — \$0.045/GB plus an hourly fee. A busy ML pipeline reading models from S3 over NAT can cost more in egress than the actual S3 bytes.

### 3.4 The "why is my service unreachable" debugging order

When a service is unreachable, check in this order:

1. **DNS** — can the client resolve the hostname?
2. **Routing** — is there a route from client to server's subnet?
3. **Security group / firewall** — does the destination allow the source IP/SG and port?
4. **Application** — is the app actually listening on the expected port and 0.0.0.0 (not 127.0.0.1)?
5. **Load balancer health check** — is the target marked healthy?

90% of "unreachable" issues are #3 or #4. Always check application binding (`0.0.0.0`, not `localhost`) when running in containers.

---

## 4. Object storage — S3, GCS, Azure Blob

Object storage is the foundation for everything: training data, model artifacts, logs, dataset versioning. Cheap (~\$0.02/GB/month), durable (11 nines on AWS), effectively infinite.

### 4.1 The basics

```python
import boto3
s3 = boto3.client("s3")

# upload
s3.upload_file("/local/path/model.pt", "myorg-models", "v1.0/model.pt")

# upload from memory
s3.put_object(Bucket="myorg-models", Key="config.json",
              Body=b'{"version": "1.0"}',
              ContentType="application/json")

# download
s3.download_file("myorg-models", "v1.0/model.pt", "/local/model.pt")

# get object body
obj = s3.get_object(Bucket="myorg-models", Key="config.json")
data = obj["Body"].read()

# list
for o in s3.list_objects_v2(Bucket="myorg-models", Prefix="v1.0/")["Contents"]:
    print(o["Key"], o["Size"])

# delete
s3.delete_object(Bucket="myorg-models", Key="old-model.pt")
```

GCS:
```python
from google.cloud import storage
client = storage.Client()
bucket = client.bucket("myorg-models")
bucket.blob("v1.0/model.pt").upload_from_filename("/local/model.pt")
data = bucket.blob("config.json").download_as_bytes()
```

Azure Blob:
```python
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential
svc = BlobServiceClient(account_url="https://mystg.blob.core.windows.net",
                         credential=DefaultAzureCredential())
container = svc.get_container_client("models")
container.upload_blob(name="v1.0/model.pt", data=open("/local/model.pt", "rb"))
```

### 4.2 Key design — flat namespace, but use prefixes wisely

Object storage is a **flat namespace**. The slashes in keys are decorative — there are no real folders. But prefixes matter for performance: list operations are scoped by prefix, and keys with shared prefixes can be partitioned for fast list.

**Key design patterns:**
- `models/{model_name}/v{version}/model.pt` — model artifacts
- `data/{date}/{shard}.parquet` — date-partitioned datasets (compatible with parquet partition discovery)
- `logs/{service}/{date}/{hour}/{instance}.log.gz` — log archives

**Avoid:** sequential prefixes (`{timestamp}-...`) on very high-throughput buckets — historically, S3 hot-spotted on key range. Modern S3 handles this, but the practice (random prefix or hash) is still common in ultra-high-throughput pipelines.

### 4.3 Storage classes — match access pattern to cost

Files have **classes**: hot, cold, archive. You pay differently for each.

| AWS class | Use case | Cost (approx) |
|---|---|---|
| S3 Standard | Active data, hot reads | $0.023/GB/mo |
| S3 Intelligent-Tiering | Unknown access pattern | auto-tiers |
| S3 Standard-IA (infrequent access) | Backup, less than monthly | $0.0125/GB/mo + retrieval |
| S3 Glacier Instant Retrieval | Archive with milliseconds retrieval | $0.004/GB/mo |
| S3 Glacier Flexible | Archive, minutes-hours retrieval | $0.0036/GB/mo |
| S3 Glacier Deep Archive | "Tape," 12+ hour retrieval | $0.00099/GB/mo |

Set **lifecycle policies** to transition automatically:
```python
s3.put_bucket_lifecycle_configuration(Bucket="myorg-models", LifecycleConfiguration={
    "Rules": [{
        "ID": "archive-old-models",
        "Status": "Enabled",
        "Filter": {"Prefix": "models/"},
        "Transitions": [
            {"Days": 90,  "StorageClass": "STANDARD_IA"},
            {"Days": 365, "StorageClass": "GLACIER"},
        ],
    }],
})
```

GCP equivalents: Standard, Nearline (≥30d), Coldline (≥90d), Archive (≥365d). Azure: Hot, Cool, Cold, Archive.

### 4.4 Versioning and immutability

```python
s3.put_bucket_versioning(Bucket="myorg-models",
                         VersioningConfiguration={"Status": "Enabled"})
```

With versioning on, every upload creates a new version; deletes are tombstones. **Critical** for: model artifacts (rollback), datasets (reproducibility), config files.

For audit/compliance: **Object Lock** (S3) — immutable retention. Cannot be deleted before the lock expiry, even by the root account.

### 4.5 Presigned URLs — let clients hit storage directly

Don't proxy uploads/downloads through your API server. Issue **presigned URLs** so clients PUT/GET directly to the bucket.

```python
url = s3.generate_presigned_url(
    "put_object",
    Params={"Bucket": "myorg-uploads", "Key": f"users/{uid}/photo.jpg",
            "ContentType": "image/jpeg"},
    ExpiresIn=900,   # 15 min
)
# Send `url` to the client; the client PUTs the file to it directly
```

The client uploads ~1GB of video, your API server does ~0 bytes of network traffic. Multiply by 10,000 clients/day → real money.

### 4.6 Encryption at rest — always on

By default, all major clouds encrypt object storage at rest with cloud-managed keys (free, transparent). For higher security/compliance, use **customer-managed keys (CMK / KMS)** — you control rotation and revocation.

```python
s3.put_object(Bucket="...", Key="...", Body=data,
              ServerSideEncryption="aws:kms",
              SSEKMSKeyId="arn:aws:kms:us-east-1:...:key/...")
```

For PII / regulated data: enforce KMS at the bucket policy level.

---

## 5. Compute — picking the right runtime

You have three buckets of compute. Choose based on the *shape of the workload*, not what's trendy.

| Shape | Use |
|---|---|
| Long-running, stateful, predictable load | **VMs** (EC2 / GCE / Azure VM) |
| Containerized HTTP services, scaling on traffic | **Managed containers** (Cloud Run, Fargate, Container Apps) |
| Many similar workloads, complex orchestration | **Kubernetes** (EKS, GKE, AKS) |
| Bursty, short-lived, event-driven | **Serverless functions** (Lambda, Cloud Functions, Azure Functions) |
| Heavy GPU training | **VMs with GPUs** or **managed batch** (SageMaker, Vertex AI, Batch) |

### 5.1 VMs — the fundamental unit

You rent a virtual machine; SSH in; run anything.

```bash
# AWS — launch with cloud-init
aws ec2 run-instances \
  --image-id ami-0abc123 \
  --instance-type m6i.large \
  --iam-instance-profile Name=my-app-role \
  --user-data file://cloud-init.yaml \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=app,Value=ml-api}]'
```

**Use VMs when:** you need full OS control, GPU drivers, kernel tuning, or custom long-running daemons. The downside: you own patching, scaling, and HA.

**Spot / Preemptible / Spot VMs.** 60-90% cheaper than on-demand; can be reclaimed at any time. Perfect for: training jobs (checkpoint frequently), batch inference, anything that can restart cleanly. **Never** for stateful services that can't tolerate interruption.

### 5.2 Managed container services — the sweet spot for most apps

In 2026, most new HTTP services should run on **Cloud Run** (GCP), **AWS Fargate / App Runner**, or **Azure Container Apps**. You hand them a container; they run it; scaling is automatic; you pay per CPU-second.

```bash
# Cloud Run example
gcloud run deploy my-api \
  --image us-docker.pkg.dev/my-project/repo/my-api:1.0.0 \
  --platform managed --region us-central1 \
  --allow-unauthenticated \
  --memory 1Gi --cpu 1 \
  --min-instances 0 --max-instances 50 \
  --concurrency 80
```

```bash
# AWS App Runner equivalent
aws apprunner create-service \
  --service-name my-api \
  --source-configuration ImageRepository={...}
```

**Why this beats Kubernetes for most teams:** zero ops. No nodes, no upgrades, no networking. Your team can focus on the app, not the platform. Trade-off: less flexibility for advanced traffic patterns or custom networking.

### 5.3 Kubernetes — when you need it

Kubernetes (EKS, GKE, AKS) is the right answer when:
- You have many services with shared infra needs.
- You need advanced scheduling (GPU pools, spot mixing, batch jobs).
- You have policy/networking requirements that managed containers can't meet.
- You're already running it for non-cloud reasons.

**The minimal K8s vocabulary:**

| Term | What it is |
|---|---|
| **Pod** | One or more containers running together (smallest deploy unit) |
| **Deployment** | Manages a set of identical pods, handles rollouts |
| **Service** | Stable network endpoint for a set of pods |
| **Ingress** | HTTP routing into the cluster |
| **ConfigMap / Secret** | Non-sensitive / sensitive config injected into pods |
| **HPA** | Horizontal Pod Autoscaler — scales by CPU/custom metric |
| **Namespace** | Logical isolation (dev / prod / per-team) |
| **Helm chart** | Templated package of K8s manifests |

A minimal Deployment + Service for a FastAPI app:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata: {name: api}
spec:
  replicas: 3
  selector: {matchLabels: {app: api}}
  template:
    metadata: {labels: {app: api}}
    spec:
      containers:
      - name: api
        image: ghcr.io/myorg/api:1.0.0
        ports: [{containerPort: 8000}]
        env:
        - name: DATABASE_URL
          valueFrom: {secretKeyRef: {name: api-secrets, key: database-url}}
        readinessProbe: {httpGet: {path: /ready, port: 8000}, periodSeconds: 5}
        livenessProbe:  {httpGet: {path: /health, port: 8000}, periodSeconds: 10}
        resources:
          requests: {cpu: 100m, memory: 256Mi}
          limits:   {cpu: 1000m, memory: 1Gi}
---
apiVersion: v1
kind: Service
metadata: {name: api}
spec:
  selector: {app: api}
  ports: [{port: 80, targetPort: 8000}]
  type: ClusterIP
```

```bash
kubectl apply -f deployment.yaml
kubectl get pods
kubectl logs -f deploy/api
kubectl scale deploy/api --replicas=10
```

For ML serving in K8s, common companions: **KServe** (model serving), **NVIDIA GPU Operator**, **Kubeflow** (training pipelines), **Argo Workflows** (DAG orchestration).

### 5.4 Serverless functions — for event-driven glue

```python
# AWS Lambda — Python 3.12 runtime
def handler(event, context):
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    key    = event["Records"][0]["s3"]["object"]["key"]
    process_uploaded_file(bucket, key)
    return {"statusCode": 200}
```

**Sweet spots:**
- **S3 / GCS object-arrival triggers** — process a file when uploaded.
- **API Gateway → Lambda** — serverless HTTP endpoint for low-traffic APIs.
- **Cron-style scheduled tasks** — EventBridge/Cloud Scheduler → function.
- **Glue between services** — quick transformations, fan-out.

**Limits to know:**
- 15-min execution cap (AWS Lambda).
- Cold starts (~100-3000ms depending on language and size).
- Max ephemeral storage (10 GB on Lambda) and memory (10 GB).
- No GPUs.

For ML inference: cold starts are usually deal-breakers unless you use provisioned concurrency. Cloud Run / App Runner are usually a better fit.

### 5.5 The decision tree, simplified

```
HTTP service, stateless?
  ├─ Low ops budget    → Cloud Run / App Runner / Container Apps
  └─ Many services + need K8s primitives  → EKS / GKE / AKS

Event-driven glue, occasional?
  └─ Lambda / Cloud Functions / Azure Functions

Long-running training / inference, GPU?
  ├─ One-off job           → Spot VM with checkpointing
  ├─ Repeatable training   → SageMaker / Vertex AI / Azure ML jobs
  └─ Persistent serving    → SageMaker endpoints / Vertex AI endpoints / managed K8s with GPU pool
```

---

## 6. Containers — the universal deploy artifact

Containers are the lingua franca of cloud compute. If you can produce a Docker image, you can run anywhere.

### 6.1 The minimal production Dockerfile (for FastAPI)

```dockerfile
# syntax=docker/dockerfile:1.7
FROM python:3.12-slim

# install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# install deps separately so caching works when only code changes
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# copy source
COPY src/ ./src/

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

# healthcheck for orchestrators that ignore it via probes (Docker Swarm, etc.)
HEALTHCHECK --interval=30s --timeout=3s CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["gunicorn", "my_api.main:app",
     "-k", "uvicorn.workers.UvicornWorker",
     "-w", "4", "-b", "0.0.0.0:8000",
     "--timeout", "30", "--graceful-timeout", "30",
     "--access-logfile", "-"]
```

**Image-size hygiene:**
- Use `-slim` or distroless base images (not full `python:3.12`).
- Multi-stage builds for compiled deps (build in fat image, copy artifacts to slim).
- One `RUN` per logical step; combine apt-get with cleanup.
- `.dockerignore` (drop `.git`, `.venv`, `__pycache__`, tests, docs).

Goal: a 200 MB image, not a 2 GB image. Pull/scale time scales with size.

### 6.2 Multi-stage builds for ML images

```dockerfile
# stage 1: builder with full toolchain
FROM python:3.12 AS builder
RUN pip install --target=/install torch numpy pandas

# stage 2: slim runtime
FROM python:3.12-slim
COPY --from=builder /install /usr/local/lib/python3.12/site-packages
COPY src/ /app/src/
CMD ["python", "/app/src/serve.py"]
```

Saves hundreds of MB. For GPU images, start from `nvidia/cuda:12.x-runtime-...` and only install what serving needs (not training).

### 6.3 Image registries

| AWS | GCP | Azure |
|---|---|---|
| ECR | Artifact Registry | ACR |

```bash
# AWS — push to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com
docker tag my-api:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/my-api:1.0.0
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/my-api:1.0.0
```

**Tag strategy:** never deploy `:latest` to production. Tag with a git SHA or semver (`:1.0.0`, `:abc1234`). Production rollbacks need known-good tags.

### 6.4 Container security — the four basics

1. **Don't run as root.** Add `USER 1000` to the Dockerfile (or `runAsNonRoot: true` in K8s).
2. **Scan images.** AWS Inspector, GCR/Artifact Registry scanning, Trivy in CI.
3. **Pin base image digests.** `FROM python:3.12-slim@sha256:...` instead of just `:3.12-slim`. Reproducible + tamper-resistant.
4. **No secrets in images.** Use mount-time secrets. Ever-popular leak: `RUN export SECRET=... && pip install ...` — that secret is in a layer.

---

## 7. Secrets and configuration

Never commit secrets. Never log secrets. Never bake secrets into images. Use a secret store.

### 7.1 The four storage tiers

| Where it lives | Use for |
|---|---|
| **Environment variables** | Non-sensitive config; or sensitive values **injected from a secret store** at runtime |
| **Cloud secret store** (Secrets Manager, Secret Manager, Key Vault) | Secrets — passwords, API keys, certificates |
| **Cloud KMS** (key management service) | The keys that encrypt other things — automatic in most cases |
| **Code / config file** | Defaults and non-secret values only |

### 7.2 AWS Secrets Manager from Python

```python
import boto3, json
sm = boto3.client("secretsmanager")

def get_db_credentials():
    resp = sm.get_secret_value(SecretId="prod/myapi/db")
    return json.loads(resp["SecretString"])

# Cache the result — secret manager calls cost money and have rate limits
from functools import lru_cache
@lru_cache(maxsize=8)
def cached_secret(name: str) -> dict:
    resp = sm.get_secret_value(SecretId=name)
    return json.loads(resp["SecretString"])
```

Secrets Manager supports automatic rotation for RDS / DocumentDB / Redshift credentials — strongly recommended.

GCP Secret Manager:
```python
from google.cloud import secretmanager
client = secretmanager.SecretManagerServiceClient()
name = "projects/my-project/secrets/db-password/versions/latest"
secret = client.access_secret_version(name=name).payload.data.decode()
```

Azure Key Vault:
```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
client = SecretClient(vault_url="https://myvault.vault.azure.net", credential=DefaultAzureCredential())
secret = client.get_secret("db-password").value
```

### 7.3 The injection pattern (orchestrator-managed)

In Kubernetes, mount secrets into pods at runtime:

```yaml
# in your Deployment
env:
- name: DATABASE_URL
  valueFrom: {secretKeyRef: {name: api-secrets, key: database-url}}
```

In ECS / Cloud Run / Container Apps, you reference a secret store entry in the task/service definition:

```yaml
# Cloud Run YAML snippet
spec:
  template:
    spec:
      containers:
      - env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              key: latest
              name: db-url-secret
```

Your code reads `os.getenv("DATABASE_URL")`. The secret never touches the image, the git repo, or your laptop.

### 7.4 Application configuration — pydantic-settings is enough

(From Module 4.) Pydantic-settings reads env vars and `.env` (in dev). In prod, the env vars come from the orchestrator pulling from the secret store. One pattern, two sources.


---

## 8. Observability — logs, metrics, traces, alerts

Your service is broken. Can you find why? That answer determines whether your incident is 5 minutes or 5 hours.

### 8.1 The three pillars

- **Logs** — discrete events ("user X did Y at time T"). Highest cardinality, expensive to store but cheap to query for specific cases.
- **Metrics** — aggregated numeric time series ("requests/s by status code"). Cheap, dashboardable, alertable; but no individual events.
- **Traces** — record of a single request flowing through services. Best for *latency root causes*.

You need all three. They serve different questions.

### 8.2 Cloud-native logging — concrete commands

```python
# AWS CloudWatch Logs from your app — you usually don't write to CW directly.
# Instead, write to stdout; the cloud collects it.

import logging, sys, json, structlog

structlog.configure(processors=[
    structlog.processors.TimeStamper(fmt="iso"),
    structlog.processors.add_log_level,
    structlog.contextvars.merge_contextvars,
    structlog.processors.JSONRenderer(),
])
logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(message)s")
log = structlog.get_logger()

log.info("request_handled", path="/users", status=200, latency_ms=42, user_id="u1")
```

The output is one line of JSON. Cloud collectors (CloudWatch agent, Cloud Logging agent, container stdout pipes) ingest stdout. Search by field is fast and cheap when logs are structured.

### 8.3 Querying logs in each cloud

```bash
# AWS — Logs Insights
fields @timestamp, @message
| filter status = 500
| stats count() by bin(5m)
```

```sql
-- GCP — Logging filter
resource.type="cloud_run_revision"
resource.labels.service_name="my-api"
severity >= ERROR
jsonPayload.user_id = "u1"
```

```kusto
// Azure — Log Analytics (KQL)
ContainerLogV2
| where ContainerName == "my-api"
| where LogLevel == "Error"
| summarize count() by bin(TimeGenerated, 5m), HostName
```

### 8.4 Metrics — instrument your service with Prometheus client

(From Module 4 §15.3.) Expose `/metrics`. Then:

- **AWS:** CloudWatch agent scrapes Prometheus endpoints (or use Managed Prometheus / Container Insights).
- **GCP:** Cloud Monitoring scrapes managed Prometheus or auto-collects from Cloud Run / GKE.
- **Azure:** Azure Monitor Managed Prometheus.

Or self-host Prometheus + Grafana — popular, free, works everywhere.

**The four golden signals** (from Google's SRE book):
1. **Latency** — p50, p95, p99 per endpoint.
2. **Traffic** — requests/sec per endpoint.
3. **Errors** — error rate, broken down by status code.
4. **Saturation** — CPU%, memory%, queue depth.

Alert on these, not on individual hosts. Hosts come and go; user-visible signals matter.

### 8.5 Tracing — OpenTelemetry across clouds

OpenTelemetry (OTel) is the cross-cloud, cross-language tracing standard. Once you instrument with OTel, you can ship traces to any backend (Cloud-managed, Datadog, Honeycomb, Jaeger).

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint="http://otel-collector:4317"))
)
FastAPIInstrumentor.instrument_app(app)
```

Then auto-instrument SQLAlchemy, httpx, Redis, etc. Each request becomes a tree of spans across services. **The single most useful debugging tool for distributed systems.**

### 8.6 Alerts — what's actually worth paging on

Three rules:

1. **Page on user-visible symptoms, not causes.** "p99 latency on /checkout > 1s for 5 min." Not "CPU > 80%."
2. **Each alert needs a runbook.** Link in the alert text.
3. **Test alerts.** Trigger them deliberately quarterly; confirm escalation works.

Common starting alerts:
- 5xx error rate > 1% for 5 min.
- p99 latency > N seconds for 5 min.
- Queue depth > X.
- Disk free < 20%.
- Health check failing on > 1 host for 5 min.
- Cost anomaly (AWS Cost Anomaly Detection / GCP Billing alerts).

---

## 9. CI/CD — build, test, deploy

The minimum viable CI/CD pipeline for a Python service:

```yaml
# .github/workflows/deploy.yml
name: deploy
on:
  push:
    branches: [main]

permissions:
  id-token: write   # OIDC to AWS
  contents: read

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync --frozen
      - run: uv run ruff check .
      - run: uv run mypy src
      - run: uv run pytest --cov=src

  build-deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/github-deploy
          aws-region: us-east-1
      - uses: aws-actions/amazon-ecr-login@v2
      - run: |
          IMAGE=123456789012.dkr.ecr.us-east-1.amazonaws.com/my-api:${{ github.sha }}
          docker build -t $IMAGE .
          docker push $IMAGE
          aws ecs update-service --cluster prod \
            --service my-api \
            --force-new-deployment \
            --task-definition my-api
```

Real-world additions:
- **Image scanning** (Trivy) before push.
- **Approval gate** for prod (`environment: production` with required reviewers).
- **Blue/green** or **canary** rollout (App Mesh, Argo Rollouts, AWS CodeDeploy, GCP traffic split).
- **Migrations before deploy** (`alembic upgrade head` step).
- **Smoke tests after deploy** (curl health check, fail and rollback if 5xx).

### 9.1 Deploy strategies, in order of safety

1. **Recreate** — kill all, start new. Downtime. Don't.
2. **Rolling update** — replace pods/tasks N at a time. The default. Some old + new traffic during the rollout.
3. **Blue/green** — full new copy, switch traffic atomically. Safer; doubles cost during deploy.
4. **Canary** — send 1%/5%/25%/100% traffic to new version, watch metrics, advance or rollback. Safest; needs traffic-splitting and good metrics.

For ML models specifically, **shadow deployments** (route copies of traffic to the new model, don't return its results) catch silent regressions without user impact.

---

## 10. Cost management — FinOps for engineers

Cloud bills go from "fine" to "huge" between two conversations. Knowing where money goes is a core engineering skill, not a finance one.

### 10.1 The five big spenders, almost universally

1. **Compute (EC2 / GCE / VM)** — right-sizing wrong is the #1 cost mistake.
2. **Egress / cross-region traffic** — moving data costs money. Same-AZ is free; cross-AZ ~\$0.01/GB; egress to internet ~\$0.05-0.09/GB.
3. **Object storage** — cheap per GB but volume adds up; lifecycle policies are easy money savers.
4. **Managed databases** — IOPS, replicas, and backups can be 10× the instance cost.
5. **GPUs** — minimum \$1-3/hr per card; shut them off when idle.

### 10.2 The five FinOps habits

1. **Tag everything** — `app`, `env`, `team`, `cost-center`. Without tags you can't attribute spend. Enforce via tag policies.
2. **Set budgets and alerts** at account/project level. \$X warning, \$Y stop. Page someone on >50% of forecast.
3. **Monthly cost review** — pull spend by service + tag; investigate the top movers. Tools: AWS Cost Explorer, GCP Billing, Azure Cost Management.
4. **Use Spot / Preemptible** for anything tolerant of interruption. Easy 60-90% savings on training and batch.
5. **Buy commitments only after data** — Savings Plans, Reserved Instances, Committed-Use Discounts give 30-60% off — but only after 3 months of stable usage. Premature commitments lose money.

```python
# AWS — programmatic cost view
import boto3
ce = boto3.client("ce")    # Cost Explorer
result = ce.get_cost_and_usage(
    TimePeriod={"Start": "2026-04-01", "End": "2026-05-01"},
    Granularity="MONTHLY",
    Metrics=["UnblendedCost"],
    GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
)
for group in result["ResultsByTime"][0]["Groups"]:
    print(group["Keys"][0], group["Metrics"]["UnblendedCost"]["Amount"])
```

### 10.3 The "ML cost reality" sub-checklist

ML adds specific cost shapes most cloud-cost dashboards don't surface:

- **Idle GPU instances.** Especially common when a notebook is left running. Auto-stop after N min idle.
- **Training jobs that don't checkpoint.** A pre-empted spot job that didn't checkpoint means re-paying for everything.
- **Model serving with provisioned concurrency you don't need.** Scale-to-zero where latency tolerates.
- **Embeddings and vector storage.** Re-embedding 100M docs is a real spend; cache aggressively.
- **LLM API calls.** Module 13 covers this in depth — but the principle is: log every call with cost; budget per feature.

---

## 11. ML serving on cloud — the platforms

Three managed ML platforms exist; each cloud's. They're roughly comparable:

| | AWS SageMaker | GCP Vertex AI | Azure ML |
|---|---|---|---|
| Notebooks | SageMaker Studio | Workbench | Notebooks |
| Training jobs | SageMaker Training | Vertex Training | Azure ML Jobs |
| Hyperparameter tuning | SageMaker HPO | Vertex Vizier | Azure ML Sweep |
| Model registry | SageMaker Model Registry | Vertex Model Registry | Azure ML Models |
| Real-time endpoints | SageMaker Endpoints | Vertex Endpoints | Online Endpoints |
| Batch inference | SageMaker Batch | Vertex Batch | Batch Endpoints |
| Pipelines | SageMaker Pipelines | Vertex Pipelines | Azure ML Pipelines |
| Feature store | SageMaker Feature Store | Vertex Feature Store | Azure ML Feature Store |

**Use a managed platform when:**
- You want one-stop training + serving + registry.
- You want managed hyperparameter tuning and pipelines.
- You don't want to operate Kubernetes for ML.

**Use plain containers (Cloud Run / Fargate / GKE) when:**
- The model is a wrapped HTTP endpoint and you don't need the full lifecycle features.
- You already have a strong K8s/CI/CD platform.
- You want maximum portability.

For LLM-era workloads, often the right pick is: **third-party API** (OpenAI/Anthropic) for foundational models + **managed container** for your application logic + **managed vector DB** for retrieval. Self-hosting an LLM only makes sense at scale or for compliance.

### 11.1 SageMaker minimal example — deploy a model behind an endpoint

```python
import sagemaker
from sagemaker.pytorch import PyTorchModel

session = sagemaker.Session()
role = "arn:aws:iam::123456789012:role/SageMakerExecRole"

model = PyTorchModel(
    model_data="s3://myorg-models/v1.0/model.tar.gz",
    role=role,
    framework_version="2.4",
    py_version="py311",
    entry_point="inference.py",   # your serving code
)

predictor = model.deploy(
    initial_instance_count=1,
    instance_type="ml.g5.xlarge",   # GPU instance
    endpoint_name="my-api-prod",
)

print(predictor.predict({"text": "hello"}))
```

The endpoint is HTTPS-fronted and auto-scales. You pay per instance-hour while the endpoint is live.

For cost control: use **serverless inference** (per-request pricing, scale to zero) when traffic is bursty.

### 11.2 Vertex AI — same idea

```python
from google.cloud import aiplatform

aiplatform.init(project="my-project", location="us-central1")

model = aiplatform.Model.upload(
    display_name="my-text-classifier",
    artifact_uri="gs://myorg-models/v1.0/",
    serving_container_image_uri="us-docker.pkg.dev/.../torch-serve:2.4",
)

endpoint = model.deploy(
    machine_type="n1-standard-4",
    accelerator_type="NVIDIA_TESLA_T4",
    accelerator_count=1,
    min_replica_count=1,
    max_replica_count=10,
)

print(endpoint.predict([{"text": "hello"}]))
```

---

## 12. GPUs in the cloud — cards, drivers, and real costs

For training and inference of any non-trivial model, you need a GPU. The cloud landscape is consolidating around NVIDIA cards in increasingly large flavors.

### 12.1 The cards (2026 reality)

| Card | Memory | Best for | Approx \$/hr (on-demand) |
|---|---|---|---|
| T4 | 16 GB | Cheapest GPU; lightweight inference | \$0.50 |
| L4 | 24 GB | Modern lightweight inference; great perf/W | \$0.80 |
| A10 / A10G | 24 GB | Mid-size training, inference | \$1.00 |
| L40S | 48 GB | Training and inference, latest mid | \$2.00 |
| A100 (40/80GB) | 40/80 GB | Serious training | \$3-4 |
| H100 (80GB) | 80 GB | Frontier training; LLMs | \$5-8 |
| H200, B200 | 144/192 GB | Largest models | constrained |

These prices vary widely; spot/preemptible reduces by 50-80%. Always check the quote at the time you provision.

### 12.2 Where to find them

- **AWS:** EC2 P/G/Inf families. SageMaker pulls from the same pool.
- **GCP:** A3 (H100), A2 (A100), G2 (L4), N1 + GPU.
- **Azure:** ND-series (H100, A100), NC (A100, T4), NV (visualization).
- **Specialty providers:** Lambda Labs, CoreWeave, Crusoe, RunPod, Modal — often cheaper, more flexible quotas, but less integration.

### 12.3 Quotas

You will hit GPU quotas. Cloud accounts default to **zero** GPU vCPUs in most regions. Request quota a week before you need it.

### 12.4 Drivers — and the container shortcut

GPU drivers + CUDA + cuDNN + framework versions form a pyramid of incompatibility. Every cloud provides **deep-learning images / containers** with a tested combination — use them. Don't hand-roll a driver install on raw VMs unless you have to.

```bash
# AWS Deep Learning AMI — comes with PyTorch + CUDA pre-installed
aws ec2 run-instances --image-id ami-0123abcdef --instance-type g5.xlarge ...

# Or use the container image
docker pull 763104351884.dkr.ecr.us-east-1.amazonaws.com/pytorch-training:2.4.0-gpu-py311
```

NVIDIA Container Toolkit lets containers see the host's GPUs (`--gpus all`). Most managed platforms set this up for you.

### 12.5 Multi-GPU and beyond

For single-host multi-GPU (one machine, 8 GPUs): training framework's data-parallel API.

For multi-host (cluster of machines, e.g. for LLM pretraining): communication libraries (NCCL, EFA on AWS), schedulers (SLURM, Ray, Kubernetes with GPU operators). Out of scope here; covered in Modules 8 and 12.

---

## 13. Reliability — multi-AZ, multi-region, DR

**Tier 0:** Single AZ. Don't.
**Tier 1:** Multi-AZ in one region. Default for any prod service. Auto Scaling Groups / managed services do this for you.
**Tier 2:** Multi-region warm standby. For data and stateless apps; harder for stateful.
**Tier 3:** Active/active across regions. Cost goes up dramatically; only when latency or DR demands it.

### 13.1 RTO and RPO

- **RTO** (Recovery Time Objective) — how quickly must we be back?
- **RPO** (Recovery Point Objective) — how much data can we lose?

For most internal services, RTO ~1h and RPO ~1h is sufficient. For payment systems, both go to seconds. The strategies (and costs) escalate fast — define them honestly.

### 13.2 Backups — not the same as multi-region

A multi-region deploy doesn't protect against a logical bug that corrupts data — it replicates the corruption. Real backups: cross-region, immutable, off-account, and **tested** by quarterly restore drills.

---

## 14. Anti-patterns

| Anti-pattern | Right way |
|---|---|
| Static cloud keys in env vars / committed | OIDC federation, workload identities |
| One AWS account for prod + dev + staging | One account/project per environment |
| `*` policies on production roles | Least-privilege via Access Analyzer / Recommender |
| Public S3 bucket "for ease" | Block public access; presigned URLs |
| Running stateful services on Spot | Spot only for fault-tolerant workloads |
| Overprovisioning 8× CPU "to be safe" | Right-size to p95; autoscale for spikes |
| `docker run --net=host` everywhere | Use proper networking; least-privileged container |
| Container as root | `USER 1000` or non-root in distroless |
| `:latest` tag in production | Immutable tags (git SHA / semver) |
| Single-AZ DB primary | Multi-AZ from day one |
| No tagging strategy | Mandatory tags via SCP / org policy |
| GPUs left running overnight | Auto-stop on idle |
| No budget alerts | Set them on every account at \$10 / \$100 / \$1000 |
| Hand-clicked infrastructure | Terraform / Pulumi from day one |
| One mega-VPC for everything | Reasonable VPC isolation (env/team) |
| Egress over public internet | VPC endpoints / Private Service Connect |
| Storing logs only in CloudWatch | Archive to S3 with lifecycle policies (cheaper, longer) |
| "We'll add monitoring later" | Add /metrics + structured logs + a dashboard before first deploy |

---

## 15. Thirty-six problems (with full structure)

Each problem follows: **Statement → Intuition → Brute force → Optimized → Complexity → Edge cases → Real-world → Follow-ups.**
**Section breakdown:** 6 IAM/security (P1–P6), 5 Storage (P7–P11), 8 Compute & containers (P12–P19), 4 Networking (P20–P23), 4 Secrets/CI/CD (P24–P27), 5 ML serving (P28–P32), 2 GPUs (P33–P34), 2 Cost/FinOps (P35–P36).

---

### Problem 1 — Read S3 from EC2 without hardcoded keys

**Statement.** Your service runs on EC2. It must read from S3 bucket `myorg-models`. Don't ship credentials in env vars.

**Solution.** Attach an instance profile (IAM role) to the EC2 instance. The default boto3 chain picks up credentials from the metadata service.

```python
# code: clean and credential-less
import boto3
s3 = boto3.client("s3")
obj = s3.get_object(Bucket="myorg-models", Key="v1/model.pt")
```

```hcl
# Terraform: role + policy + instance profile
resource "aws_iam_role" "ec2_app" {
  name = "ec2-app-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{Effect="Allow", Principal={Service="ec2.amazonaws.com"},
                  Action="sts:AssumeRole"}]
  })
}

resource "aws_iam_role_policy" "ec2_app" {
  role = aws_iam_role.ec2_app.id
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{Effect="Allow", Action=["s3:GetObject"],
                  Resource="arn:aws:s3:::myorg-models/*"}]
  })
}

resource "aws_iam_instance_profile" "ec2_app" {
  name = "ec2-app"
  role = aws_iam_role.ec2_app.name
}
```

**Real-world.** This is the *default* pattern in 2026. Static keys for workloads is a code smell.

**Follow-ups.** GCP equivalent (Compute service account). Azure (Managed Identity). EKS pod identity (IRSA).

---

### Problem 2 — Write a least-privilege S3 policy

**Statement.** Service needs to: read all objects under `s3://myorg-uploads/users/{user}/*`, write objects under same prefix, list any objects under `users/`. Nothing else.

**Solution.**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ListUserUploads",
      "Effect": "Allow",
      "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::myorg-uploads",
      "Condition": {"StringLike": {"s3:prefix": ["users/*"]}}
    },
    {
      "Sid": "ReadWriteUserObjects",
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
      "Resource": "arn:aws:s3:::myorg-uploads/users/*"
    }
  ]
}
```

**Why.** `s3:ListBucket` is a bucket-level action; the others are object-level. Mixing them up causes "Access Denied" with confusing messages.

**Real-world.** "We had to grant `s3:*` because nothing else worked" is almost always wrong — the prefix conditions just need careful reading.

**Follow-ups.** Tag-based access control (`aws:RequestTag`). Per-user constraints with `${aws:username}`.

---

### Problem 3 — Federate GitHub Actions to AWS without static keys

**Statement.** CI runs in GitHub Actions, deploys to AWS. Don't store AWS access keys.

**Solution.**

```hcl
data "aws_caller_identity" "current" {}

resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]
}

resource "aws_iam_role" "github_deploy" {
  name = "github-deploy"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Principal = {Federated = aws_iam_openid_connect_provider.github.arn},
      Action = "sts:AssumeRoleWithWebIdentity",
      Condition = {
        StringEquals = {
          "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
        },
        StringLike = {
          "token.actions.githubusercontent.com:sub" = "repo:myorg/myrepo:*"
        }
      }
    }]
  })
}
```

In the workflow:
```yaml
permissions:
  id-token: write
  contents: read
steps:
- uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: ${{ secrets.AWS_DEPLOY_ROLE_ARN }}
    aws-region: us-east-1
```

**Real-world.** Eliminates an entire class of secret-leak incidents. Every credential is short-lived, scoped to one workflow run, attributable in CloudTrail.

**Follow-ups.** Restrict by branch (`...:ref:refs/heads/main`). GCP Workload Identity Federation. Azure OIDC for pipelines.

---

### Problem 4 — Secure inter-service auth in K8s with IRSA

**Statement.** A pod in EKS needs to publish to SQS. Without IAM access keys.

**Solution.**

```hcl
resource "aws_iam_role" "pod_publisher" {
  name = "pod-publisher"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Principal = {Federated = aws_iam_openid_connect_provider.eks.arn},
      Action = "sts:AssumeRoleWithWebIdentity",
      Condition = {
        StringEquals = {
          "${replace(aws_iam_openid_connect_provider.eks.url, "https://", "")}:sub":
            "system:serviceaccount:my-ns:my-publisher"
        }
      }
    }]
  })
}
```

```yaml
# k8s — bind ServiceAccount to the IAM role
apiVersion: v1
kind: ServiceAccount
metadata:
  name: my-publisher
  namespace: my-ns
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789012:role/pod-publisher
---
apiVersion: apps/v1
kind: Deployment
metadata: {name: publisher, namespace: my-ns}
spec:
  template:
    spec:
      serviceAccountName: my-publisher    # this gives pods the role
      containers: [...]
```

The pod's boto3 calls now use temporary credentials from STS, scoped to that role.

**Real-world.** IRSA (IAM Roles for Service Accounts) is the standard pod-level auth in EKS. GKE has Workload Identity; AKS has AAD Pod Identity / Workload Identity.

**Follow-ups.** Service-mesh mTLS for in-cluster traffic. Per-namespace IAM boundaries.

---

### Problem 5 — Detect and shrink overly-broad permissions

**Statement.** A service has policies granting `s3:*` and `dynamodb:*`. Find the actions actually used in the last 90 days; propose a tighter policy.

**Solution.** Use **AWS IAM Access Analyzer** (analogous tools: GCP Policy Recommender, Azure Privileged Identity Management).

```python
import boto3
ia = boto3.client("accessanalyzer")

# generate a policy from CloudTrail history
job = ia.start_policy_generation(
    policyGenerationDetails={
        "principalArn": "arn:aws:iam::123456789012:role/my-app"
    },
    cloudTrailDetails={
        "trails": [{"cloudTrailArn": "arn:aws:cloudtrail:...:trail/org"}],
        "accessRole": "arn:aws:iam::123456789012:role/AccessAnalyzerRole",
        "startTime": "2026-01-01T00:00:00Z",
    },
)
job_id = job["jobId"]
# poll until ready, then ia.get_generated_policy(jobId=job_id)
```

**Real-world.** Most teams set this up once → identify the over-broad roles → rewrite policies → repeat quarterly. It's the structured way to enforce least-privilege without breaking things.

**Follow-ups.** Service control policies that *deny* dangerous actions org-wide. Permissions boundaries that cap what a role can do regardless of attached policies.

---

### Problem 6 — Block S3 public access at the org level

**Statement.** Prevent any user, in any account, from making any S3 bucket publicly readable.

**Solution.**
```hcl
resource "aws_organizations_policy" "block_public_s3" {
  name = "block-public-s3"
  type = "SERVICE_CONTROL_POLICY"
  content = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect   = "Deny",
      Action   = ["s3:PutBucketPublicAccessBlock", "s3:DeleteBucketPublicAccessBlock"],
      Resource = "*",
      Condition = {
        BoolIfExists = {
          "s3:PublicAccessBlock:BlockPublicAcls": "false"
        }
      }
    }]
  })
}

resource "aws_organizations_policy_attachment" "all" {
  policy_id = aws_organizations_policy.block_public_s3.id
  target_id = aws_organizations_organization.main.roots[0].id
}
```

Plus account-level:
```python
import boto3
s3control = boto3.client("s3control")
s3control.put_public_access_block(
    AccountId="123456789012",
    PublicAccessBlockConfiguration={
        "BlockPublicAcls": True, "IgnorePublicAcls": True,
        "BlockPublicPolicy": True, "RestrictPublicBuckets": True,
    },
)
```

**Real-world.** This single setting prevents 90% of "company X leaked Y million records" incidents. Enable everywhere, opt-out per bucket only when you have a CDN/special use case.

**Follow-ups.** Equivalent: GCP Organization Policy `storage.publicAccessPrevention`; Azure Storage Account "allow public access" disabled at subscription scope.

---

### Problem 7 — Upload a model artifact to S3 with versioning

**Statement.** Versioned upload of `model.pt` to `s3://myorg-models/v1.0/`, KMS-encrypted, with metadata.

**Solution.**
```python
import boto3, hashlib

s3 = boto3.client("s3")
BUCKET = "myorg-models"
KEY = "v1.0/model.pt"
KMS_KEY = "arn:aws:kms:us-east-1:123456789012:key/abc-..."

with open("/local/model.pt", "rb") as f:
    body = f.read()
sha256 = hashlib.sha256(body).hexdigest()

resp = s3.put_object(
    Bucket=BUCKET, Key=KEY, Body=body,
    ServerSideEncryption="aws:kms", SSEKMSKeyId=KMS_KEY,
    Metadata={
        "framework": "pytorch", "version": "1.0.0",
        "sha256": sha256, "trained-by": "ada@myorg.com",
    },
    ContentType="application/octet-stream",
)
print("VersionId:", resp["VersionId"])
```

**Real-world.** Versioning + immutable storage is the floor for reproducible ML. Metadata lets you audit "who trained this model?" three years later.

**Follow-ups.** Use `s3.generate_presigned_url(...)` for the trainer to PUT directly. Use the S3 inventory to catalog all model versions in a manifest.

---

### Problem 8 — Stream a 10 GB file from S3 without OOM

**Statement.** Process a 10 GB JSONL file from S3, line-by-line, on a 1 GB instance.

**Solution.**
```python
import boto3, json

s3 = boto3.client("s3")
resp = s3.get_object(Bucket="myorg-data", Key="big.jsonl")
body = resp["Body"]      # botocore.response.StreamingBody — supports iter_lines

count = 0
for raw in body.iter_lines(chunk_size=64 * 1024):
    if not raw: continue
    obj = json.loads(raw)
    process(obj)
    count += 1
print(count)
```

**Real-world.** Don't `read()` whole multi-GB files into memory. `iter_lines` (or `iter_chunks` for binary) keeps memory bounded.

**Follow-ups.** Multipart download (`download_fileobj` with concurrency for raw bytes). Range requests for partial reads. Use S3 Select / Athena for filtering server-side.

---

### Problem 9 — Generate a presigned URL for direct browser upload

**Statement.** Web client should upload a file directly to S3, bypassing your API server.

**Solution.**
```python
url = s3.generate_presigned_url(
    "put_object",
    Params={
        "Bucket": "myorg-uploads",
        "Key":    f"users/{user_id}/{uuid.uuid4()}.bin",
        "ContentType": "application/octet-stream",
    },
    ExpiresIn=900,    # 15 min
)
# return url to client; client does:  PUT url with the file body
```

For multipart uploads (>5 GB or unknown size), use **POST presigned URLs** with policy constraints:
```python
post = s3.generate_presigned_post(
    Bucket="myorg-uploads",
    Key="users/${filename}",
    Fields={"acl": "private"},
    Conditions=[
        {"acl": "private"},
        ["content-length-range", 1, 100 * 1024 * 1024],   # max 100 MB
        ["starts-with", "$Content-Type", "image/"],
    ],
    ExpiresIn=900,
)
```

**Real-world.** Saves bandwidth on your API servers; reduces latency; isolates upload failures from app failures. Standard pattern at every consumer app with media uploads.

**Follow-ups.** Fanout via S3 event notifications (S3 ObjectCreated → Lambda → DB row insert). Virus scan via S3 trigger.

---

### Problem 10 — Lifecycle policy to archive old data

**Statement.** Move objects older than 90 days to Glacier; delete after 7 years.

**Solution.**
```python
s3.put_bucket_lifecycle_configuration(
    Bucket="myorg-logs",
    LifecycleConfiguration={
        "Rules": [{
            "ID": "archive-and-delete",
            "Status": "Enabled",
            "Filter": {"Prefix": "logs/"},
            "Transitions": [
                {"Days": 30, "StorageClass": "STANDARD_IA"},
                {"Days": 90, "StorageClass": "GLACIER"},
            ],
            "Expiration": {"Days": 7 * 365},
            "AbortIncompleteMultipartUpload": {"DaysAfterInitiation": 7},
        }],
    },
)
```

**Real-world.** Without lifecycle policies, old data sits in expensive storage. The `AbortIncompleteMultipartUpload` rule alone can recover real money — failed uploads accumulate invisibly.

**Follow-ups.** Per-prefix rules. Intelligent-Tiering as a hands-off alternative. GCP equivalent: `Lifecycle.Rule` on bucket; Azure: management policies on storage account.

---

### Problem 11 — Mirror an S3 bucket cross-region for DR

**Statement.** Replicate `myorg-prod-data` from `us-east-1` to `eu-west-1`.

**Solution.**
```hcl
resource "aws_s3_bucket" "src" {
  bucket = "myorg-prod-data"
}

resource "aws_s3_bucket" "dst" {
  bucket   = "myorg-prod-data-dr"
  provider = aws.eu_west_1
}

resource "aws_s3_bucket_versioning" "src" { bucket = aws_s3_bucket.src.id; versioning_configuration { status = "Enabled" } }
resource "aws_s3_bucket_versioning" "dst" { bucket = aws_s3_bucket.dst.id; versioning_configuration { status = "Enabled" } }

resource "aws_s3_bucket_replication_configuration" "src" {
  role   = aws_iam_role.replication.arn
  bucket = aws_s3_bucket.src.id
  rule {
    id       = "all"
    status   = "Enabled"
    priority = 1
    filter {}
    destination {
      bucket        = aws_s3_bucket.dst.arn
      storage_class = "STANDARD_IA"
    }
    delete_marker_replication { status = "Enabled" }
  }
}
```

**Real-world.** Cross-Region Replication (CRR) is async (typically <15 min). For RPO=0 you'd need synchronous replication, which is exotic and expensive. Most teams accept CRR + recovery drills.

**Follow-ups.** Two-way replication (each region active). Object Lock + Compliance mode for immutability. Cost: replication + cross-region transfer ~ \$0.02/GB.

---

### Problem 12 — Build a tight production Dockerfile

**Statement.** Produce an image for a FastAPI service. Target: <250 MB, non-root user, multi-stage, fast cold start.

**Solution.**
```dockerfile
# syntax=docker/dockerfile:1.7

# Stage 1: builder — compile/install everything heavy
FROM python:3.12-slim AS builder
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Stage 2: runtime — slim, no build tools
FROM python:3.12-slim AS runtime
RUN groupadd --gid 1000 app && useradd --uid 1000 --gid app --no-create-home --shell /sbin/nologin app
WORKDIR /app
COPY --from=builder /app/.venv ./.venv
COPY src ./src
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
USER app
EXPOSE 8000
CMD ["gunicorn", "my_api.main:app", "-k", "uvicorn.workers.UvicornWorker",
     "-w", "4", "-b", "0.0.0.0:8000", "--timeout", "30", "--access-logfile", "-"]
```

`.dockerignore`:
```
.git
.venv
__pycache__
*.pyc
tests/
docs/
```

**Real-world.** A 3 GB image takes minutes to pull on every node start; a 250 MB image takes seconds. At scale this directly affects autoscaling speed and rolling-deploy time.

**Follow-ups.** Distroless base for even smaller (`gcr.io/distroless/python3-debian12`). Image-scan in CI (Trivy). Sign images with Cosign/SLSA.

---

### Problem 13 — Deploy a container to Cloud Run

**Solution.**
```bash
# build and push
gcloud builds submit --tag us-docker.pkg.dev/$PROJ/repo/my-api:$(git rev-parse --short HEAD)

# deploy
gcloud run deploy my-api \
  --image us-docker.pkg.dev/$PROJ/repo/my-api:$(git rev-parse --short HEAD) \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 1Gi --cpu 1 \
  --min-instances 0 --max-instances 50 \
  --concurrency 80 \
  --timeout 300 \
  --set-env-vars "ENV=prod" \
  --set-secrets "DATABASE_URL=db-url:latest,JWT_SECRET=jwt-secret:latest" \
  --service-account my-api-sa@$PROJ.iam.gserviceaccount.com \
  --execution-environment gen2
```

**Notes:**
- `--min-instances 0` scales to zero (cheap, with cold starts).
- `--concurrency 80` — each instance handles up to 80 concurrent requests (raise for I/O-bound async).
- `--set-secrets` injects from Secret Manager at runtime.
- `--service-account` runs with that identity (workload identity).

**Real-world.** This is one of the simplest viable production deploys. AWS App Runner and Azure Container Apps are conceptually identical; ECS Fargate is similar but more configurable.

**Follow-ups.** Traffic split for canary (`--no-traffic`, then `gcloud run services update-traffic ... --to-revisions LATEST=10`). Service-to-service auth via signed identity tokens.

---

### Problem 14 — Deploy to ECS Fargate via Terraform

**Solution (skeleton).**
```hcl
resource "aws_ecs_cluster" "main" { name = "prod" }

resource "aws_ecs_task_definition" "api" {
  family                   = "api"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.exec.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([{
    name      = "api"
    image     = "${var.ecr_uri}:${var.image_tag}"
    portMappings = [{containerPort = 8000, protocol = "tcp"}]
    environment = [{name = "ENV", value = "prod"}]
    secrets = [
      {name = "DATABASE_URL", valueFrom = aws_secretsmanager_secret.db.arn},
      {name = "JWT_SECRET",   valueFrom = aws_secretsmanager_secret.jwt.arn},
    ]
    logConfiguration = {
      logDriver = "awslogs",
      options = {
        awslogs-group  = aws_cloudwatch_log_group.api.name,
        awslogs-region = "us-east-1",
        awslogs-stream-prefix = "api",
      }
    }
    healthCheck = {
      command  = ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
      interval = 30, timeout = 5, retries = 3, startPeriod = 30
    }
  }])
}

resource "aws_ecs_service" "api" {
  name            = "api"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = 3
  launch_type     = "FARGATE"
  network_configuration {
    subnets          = var.private_subnets
    security_groups  = [aws_security_group.api.id]
    assign_public_ip = false
  }
  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "api"
    container_port   = 8000
  }
  deployment_minimum_healthy_percent = 100
  deployment_maximum_percent         = 200    # blue/green during deploy
}
```

**Real-world.** Pair with an ALB target group for traffic; CloudWatch alarms for autoscaling; CodeDeploy for blue/green strategy.

**Follow-ups.** Service auto-scaling on CPU. ALB rules per path/host for multiple services. Service Connect for service-to-service auth.

---

### Problem 15 — A minimal K8s deployment

**Solution.**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata: {name: api, namespace: prod}
spec:
  replicas: 3
  strategy: {type: RollingUpdate, rollingUpdate: {maxSurge: 1, maxUnavailable: 0}}
  selector: {matchLabels: {app: api}}
  template:
    metadata: {labels: {app: api}}
    spec:
      serviceAccountName: api    # bound to IAM role via IRSA
      containers:
      - name: api
        image: ghcr.io/myorg/api:1.0.0
        ports: [{containerPort: 8000}]
        envFrom:
        - secretRef: {name: api-secrets}
        readinessProbe: {httpGet: {path: /ready, port: 8000}, periodSeconds: 5}
        livenessProbe:  {httpGet: {path: /health, port: 8000}, periodSeconds: 10, failureThreshold: 3}
        resources:
          requests: {cpu: 100m, memory: 256Mi}
          limits:   {cpu: 1000m, memory: 1Gi}
---
apiVersion: v1
kind: Service
metadata: {name: api, namespace: prod}
spec:
  selector: {app: api}
  ports: [{port: 80, targetPort: 8000}]
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata: {name: api, namespace: prod}
spec:
  scaleTargetRef: {apiVersion: apps/v1, kind: Deployment, name: api}
  minReplicas: 3
  maxReplicas: 30
  metrics:
  - type: Resource
    resource: {name: cpu, target: {type: Utilization, averageUtilization: 70}}
```

```bash
kubectl apply -f api.yaml -n prod
kubectl rollout status deploy/api -n prod
kubectl logs -f deploy/api -n prod
```

**Real-world.** The minimum viable K8s deployment. Production additions: PodDisruptionBudget, NetworkPolicy, PriorityClass, Topology spread constraints.

**Follow-ups.** KEDA for custom-metric autoscaling. Argo Rollouts for canary. ServiceMonitor for Prometheus.

---

### Problem 16 — Choose: Cloud Run vs ECS vs K8s for a new service

**Scenario.** Single FastAPI service, will probably scale to a few thousand RPS, small team.

**Decision.**
- **Cloud Run / App Runner / Container Apps** — start here. Zero ops, fits the workload.
- **ECS Fargate** — pick if you need ALB-level routing, VPC-private services, or AWS-native integration.
- **EKS / GKE / AKS** — pick only if you have ≥3 services that share infra, or you already operate K8s.

**Why.** "Premature K8s" is the single most common over-engineering pattern in 2026. Most apps do not need pods, helm charts, ingress controllers, and service meshes. Cloud-managed containers serve them perfectly.

**Real-world.** Many teams adopt K8s for one service and pay the operational tax forever. Don't, unless the second service is already on the way.

**Follow-ups.** Migration paths between options (most managed services let you switch with the same Docker image). Multi-runtime patterns.

---

### Problem 17 — Auto-scale on RPS, not CPU

**Statement.** Your service is async I/O-bound; CPU stays at 30% even at peak. CPU-based HPA never scales it up. Latency spikes anyway.

**Solution.** Scale on RPS or queue depth (KEDA on K8s; Application Auto Scaling on ECS; Cloud Run does this natively).

```yaml
# K8s + KEDA — scale based on Prometheus query (RPS)
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata: {name: api}
spec:
  scaleTargetRef: {name: api}
  minReplicaCount: 3
  maxReplicaCount: 50
  triggers:
  - type: prometheus
    metadata:
      serverAddress: http://prometheus:9090
      query: sum(rate(http_requests_total{service="api"}[1m]))
      threshold: "100"   # scale to keep ~100 RPS per pod
```

**Real-world.** Async services with low CPU but lots of in-flight requests are a common HPA failure case. Pick a metric that reflects user-visible load.

**Follow-ups.** Custom metrics (active connections, queue length). Predictive scaling.

---

### Problem 18 — Graceful shutdown in a container

**Statement.** Rolling deploy drops a few requests when pods restart. Make it zero.

**Solution.**

App side (FastAPI, see Module 4 §16):
```python
# lifespan handler closes resources cleanly on shutdown
```

K8s side:
```yaml
spec:
  terminationGracePeriodSeconds: 60   # default 30s; raise if your requests are slow
  containers:
  - name: api
    lifecycle:
      preStop:
        exec:
          command: ["sh", "-c", "sleep 5"]    # let LB drain before SIGTERM
```

Plus: Gunicorn `--graceful-timeout 30 --timeout 30` so workers finish in-flight requests on SIGTERM.

**Real-world.** "We have rolling deploys and it's fine" but every release drops 0.1% of requests — at 1M requests/day that's 1000 errors per release. Graceful shutdown is the fix.

**Follow-ups.** Connection draining at the LB. Long-running requests need a separate strategy (deadline propagation, async work queue).

---

### Problem 19 — Run a one-off job (training, migration, batch)

**Statement.** Run a Python training script that takes 4 hours, on demand.

**Three options, in increasing complexity:**

1. **Manually:** boot a Spot VM with cloud-init, SSH in, run, shutdown.
2. **K8s Job:**
```yaml
apiVersion: batch/v1
kind: Job
metadata: {name: train-job}
spec:
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: train
        image: ghcr.io/myorg/training:1.0
        command: ["python", "/app/train.py"]
        resources: {requests: {nvidia.com/gpu: 1}}
      nodeSelector: {gpu: a10}
  backoffLimit: 2
```

3. **AWS Batch / GCP Batch / SageMaker Training Job / Vertex Training Job** — submit and forget; the platform schedules and reaps.

```python
# AWS Batch via boto3
import boto3
batch = boto3.client("batch")
job = batch.submit_job(
    jobName="train-2026-04-27",
    jobQueue="gpu-queue",
    jobDefinition="train-pytorch",
    containerOverrides={"command": ["python", "/app/train.py", "--epochs", "10"]},
)
```

**Real-world.** For repeatable workflows, use Batch / SageMaker / Vertex / Argo Workflows — they handle queueing, retries, GPU pool reuse. For one-off experiments, a Spot VM is fine.

**Follow-ups.** Checkpoint to S3 every N minutes so spot interruption doesn't lose hours.

---

### Problem 20 — VPC for an HTTP service

**Statement.** Set up a minimal VPC with public subnets (LB) and private subnets (app + DB) across two AZs.

**Solution (Terraform sketch).**
```hcl
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
}

# 2 public + 2 private subnets across 2 AZs
locals {
  azs = ["us-east-1a", "us-east-1b"]
}

resource "aws_subnet" "public" {
  count = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index}.0/24"
  availability_zone = local.azs[count.index]
  map_public_ip_on_launch = true
}

resource "aws_subnet" "private" {
  count = 2
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.${count.index + 10}.0/24"
  availability_zone = local.azs[count.index]
}

resource "aws_internet_gateway" "main" { vpc_id = aws_vpc.main.id }

resource "aws_nat_gateway" "main" {
  count         = 2
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id
}

# routing tables omitted for brevity
```

**Real-world.** Most cloud providers have a "default VPC" that's good enough for dev. For prod, define your own — names and CIDR ranges that don't collide with other VPCs you'll peer with later.

**Follow-ups.** VPC endpoints for S3/DynamoDB (free, no NAT charges). Transit Gateway for many VPCs. Single NAT GW vs per-AZ tradeoff (cost vs availability).

---

### Problem 21 — Add a VPC endpoint to skip NAT charges for S3

**Statement.** Your service in private subnets reads heavily from S3. NAT egress is costing \$2k/month.

**Solution.**
```hcl
resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.us-east-1.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = aws_route_table.private[*].id
}
```

This is a **gateway endpoint** — free, attaches to route tables, traffic to S3 stays on AWS backbone. After applying, S3 traffic no longer goes through the NAT Gateway.

```python
# verify in your app
import socket
print(socket.gethostbyname("myorg-models.s3.us-east-1.amazonaws.com"))
# resolves to a private IP within the VPC after the endpoint is attached
```

**Real-world.** Easiest, biggest cost win on a busy data pipeline. Same applies to DynamoDB. For other services (Secrets Manager, ECR, etc.) use **interface endpoints** (PrivateLink) — also save NAT cost but cost \$0.01/hour each.

**Follow-ups.** Usage-based decision: if NAT egress > N GB/month, an interface endpoint pays for itself. GCP equivalent: Private Google Access.

---

### Problem 22 — Internal-only HTTPS service

**Statement.** Service should be reachable from other services in the same VPC, never from the internet.

**Solution.** Internal load balancer (`internal=true` in AWS / "internal" load balancer in GCP/Azure). Place the LB in private subnets; do not associate Elastic IPs.

```hcl
resource "aws_lb" "internal" {
  name               = "api-internal"
  internal           = true
  load_balancer_type = "application"
  security_groups    = [aws_security_group.lb.id]
  subnets            = aws_subnet.private[*].id
}
```

For HTTPS internally, issue a private CA certificate (AWS Private CA / GCP Internal CA) — your services trust the private CA root.

**Real-world.** Most service-to-service traffic should be internal. External LBs only for public APIs and end-user traffic.

**Follow-ups.** Service Connect / Service Mesh for service-to-service mTLS. Private DNS zones.

---

### Problem 23 — Debug "connection refused"

**Statement.** Your service deployed; load balancer health check fails with "connection refused."

**Diagnosis checklist:**
1. **App is listening on `0.0.0.0`, not `127.0.0.1`.** Inside containers, `localhost` is unreachable from outside the container.
2. **Container exposes the port.** `EXPOSE 8000` in Dockerfile; `containerPort: 8000` in K8s; `portMappings` in ECS.
3. **Health check path returns 200.** Hit it from inside the container: `curl localhost:8000/health`.
4. **Security group allows the LB's source.** In AWS, this is usually "allow from the LB's SG, port 8000."
5. **NACLs don't deny.** Rare cause, but check both directions.

```python
# canonical FastAPI bind:
# uvicorn my_api.main:app --host 0.0.0.0 --port 8000
```

**Real-world.** The first three are 90% of cases. Item 1 is the single most common bug in containers.

**Follow-ups.** Use `kubectl exec` / `aws ecs execute-command` to shell into a running container and curl from inside.

---

### Problem 24 — Inject a database secret at runtime, with rotation

**Statement.** App needs `DATABASE_URL`. Don't hardcode; rotate without redeploy.

**Solution (AWS pattern).**

Store in Secrets Manager:
```python
sm = boto3.client("secretsmanager")
sm.create_secret(
    Name="prod/api/db",
    SecretString=json.dumps({"username": "appuser", "password": "...",
                              "host": "...", "port": 5432, "dbname": "myapp"}),
)
```

Inject in ECS task definition:
```json
"secrets": [{
    "name": "DATABASE_URL",
    "valueFrom": "arn:aws:secretsmanager:us-east-1:...:secret:prod/api/db:url::"
}]
```

In code, read `os.getenv("DATABASE_URL")` — refreshed on task restart.

For *zero-restart* rotation, fetch and cache in the app:
```python
import boto3, json, time

sm = boto3.client("secretsmanager")
_cache = {"value": None, "expires": 0}

def get_db_password() -> str:
    if time.time() < _cache["expires"]:
        return _cache["value"]
    resp = sm.get_secret_value(SecretId="prod/api/db")
    _cache["value"]   = json.loads(resp["SecretString"])["password"]
    _cache["expires"] = time.time() + 300        # 5 min cache
    return _cache["value"]
```

**Real-world.** Most managed databases (RDS, Cloud SQL with IAM auth) don't even need passwords — IAM-based DB auth gets you fully credentialed without secrets at all.

**Follow-ups.** Automatic rotation via Secrets Manager rotation function. KMS encryption for the secret itself.

---

### Problem 25 — Use IAM auth to RDS Postgres (no passwords)

**Statement.** Eliminate database passwords entirely.

**Solution.**
```python
import boto3
import psycopg
from urllib.parse import quote

rds = boto3.client("rds")
token = rds.generate_db_auth_token(
    DBHostname="myorg-prod.xxxxx.us-east-1.rds.amazonaws.com",
    Port=5432, DBUsername="appuser", Region="us-east-1",
)

conn = psycopg.connect(
    host="myorg-prod.xxxxx.us-east-1.rds.amazonaws.com",
    port=5432, dbname="myapp", user="appuser",
    password=token,                              # 15-min token
    sslmode="verify-full",
    sslrootcert="/etc/ssl/certs/rds-ca.pem",
)
```

The IAM role attached to the workload must have `rds-db:connect`. The token is valid for 15 minutes.

**Real-world.** Security-team-friendly: no secrets to rotate, every connection auditable in CloudTrail. Performance: token generation is cheap; cache for ~10 min then refresh.

**Follow-ups.** SQLAlchemy event hook to refresh tokens on connection. GCP Cloud SQL IAM auth (similar). Azure equivalent: Microsoft Entra ID auth for Azure DB.

---

### Problem 26 — A safe CI/CD with environment promotion

**Statement.** Pipeline: PR → tests → build image → deploy to staging on merge to `main` → manual approval → deploy to prod.

**Solution (skeleton).**
```yaml
name: deploy
on:
  push: {branches: [main]}
  pull_request:

permissions: {id-token: write, contents: read}

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync --frozen
      - run: uv run ruff check && uv run mypy src && uv run pytest --cov=src
      - uses: aquasecurity/trivy-action@master
        with: {image-ref: 'ghcr.io/myorg/api:${{ github.sha }}', severity: 'CRITICAL,HIGH'}

  build:
    if: github.ref == 'refs/heads/main'
    needs: test
    runs-on: ubuntu-latest
    outputs: {image: ${{ steps.meta.outputs.image }}}
    steps:
      - uses: actions/checkout@v4
      - uses: aws-actions/configure-aws-credentials@v4
        with: {role-to-assume: ${{ vars.BUILD_ROLE }}, aws-region: us-east-1}
      - uses: aws-actions/amazon-ecr-login@v2
      - id: meta
        run: |
          IMAGE=${{ vars.ECR_URI }}:${{ github.sha }}
          echo "image=$IMAGE" >> $GITHUB_OUTPUT
          docker build -t $IMAGE .
          docker push $IMAGE

  deploy-staging:
    needs: build
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - run: |
          aws ecs update-service --cluster staging \
            --service my-api --force-new-deployment \
            --task-definition my-api

  deploy-prod:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment: production    # github environments require manual approval
    steps:
      - run: aws ecs update-service ...
```

GitHub Environments provide manual approval gates. Pair with CodeDeploy (AWS) or Argo Rollouts (K8s) for canary in prod.

**Real-world.** Most production teams converge on this shape: PR tests → main deploys to staging → manual gate → prod canary.

**Follow-ups.** Auto-rollback on alert. Smoke tests post-deploy. Migration step before app deploy.

---

### Problem 27 — Database migration safely in CI

**Statement.** Apply Alembic migrations as part of deploy, without downtime.

**Solution.** Two practices:

1. **Always run migrations before** the app deploy (so the new app version sees the new schema).
2. **Migrations must be backward-compatible** (Module 3 §8.3) — the *old* app version also runs against the new schema during the rollout.

In CI:
```yaml
- name: Migrate DB
  env: {DATABASE_URL: ${{ secrets.STAGING_DB_URL }}}
  run: uv run alembic upgrade head
```

Run from a job runner that has DB network access. After success, deploy the app. If migration fails, abort deploy.

**Real-world.** Couples to graceful shutdown + rolling deploy: with backward-compatible migrations and proper rollouts, schema changes happen with zero downtime.

**Follow-ups.** Online schema change tools for big tables (`gh-ost`, `pt-online-schema-change`). Maintenance windows for irreversible changes.

---

### Problem 28 — Deploy a model behind a SageMaker endpoint

**Solution.**
```python
import sagemaker
from sagemaker.pytorch import PyTorchModel

session = sagemaker.Session()
ROLE = "arn:aws:iam::123456789012:role/SageMakerExec"

# inference.py — model handlers (model_fn, input_fn, predict_fn, output_fn)
# packaged in your code/inference.py

model = PyTorchModel(
    model_data="s3://myorg-models/v1.0/model.tar.gz",
    role=ROLE,
    entry_point="inference.py",
    source_dir="code",
    framework_version="2.4",
    py_version="py311",
)

# autoscaling endpoint
predictor = model.deploy(
    initial_instance_count=1,
    instance_type="ml.g5.xlarge",
    endpoint_name="my-classifier",
)

# inference
out = predictor.predict({"text": "hello"})
```

For cost: enable autoscaling with `boto3.client("application-autoscaling")` to scale to zero on idle (or use serverless inference for bursty traffic).

**Real-world.** SageMaker handles auto-scaling, A/B variants, model registry, audit. The cost is a SageMaker premium over raw EC2 — ~10-20%. Worth it for teams without an existing ML platform.

**Follow-ups.** Multi-model endpoints (host many small models on one). Async inference (queue-based, no timeout). Shadow deployments for A/B testing.

---

### Problem 29 — Vertex AI deploy via Python

**Solution.**
```python
from google.cloud import aiplatform

aiplatform.init(project="my-project", location="us-central1")

model = aiplatform.Model.upload(
    display_name="text-classifier-v1",
    artifact_uri="gs://myorg-models/v1.0/",
    serving_container_image_uri="us-docker.pkg.dev/proj/repo/my-server:1.0",
    serving_container_predict_route="/predict",
    serving_container_health_route="/health",
    serving_container_ports=[8080],
)

endpoint = aiplatform.Endpoint.create(display_name="text-classifier-prod")

model.deploy(
    endpoint=endpoint,
    machine_type="n1-standard-4",
    accelerator_type="NVIDIA_TESLA_T4",
    accelerator_count=1,
    min_replica_count=1,
    max_replica_count=10,
    traffic_percentage=100,
)
```

Built-in: traffic split for A/B (deploy a second model to the same endpoint with `traffic_split={"v1": 90, "v2": 10}`), monitoring, model registry.

**Real-world.** Vertex Model Registry + endpoints is the cleanest E2E flow on GCP, especially when feeding from BigQuery features.

**Follow-ups.** Vertex Pipelines for orchestration. Online prediction with feature store. Custom Python container if you want full control over the server.

---

### Problem 30 — A/B test two model versions in production

**Statement.** Deploy v2 alongside v1; route 10% of traffic to v2; auto-roll if error rate spikes.

**Solution.**

On any modern platform (SageMaker variants, Vertex traffic split, K8s with Argo Rollouts):

```python
# SageMaker: production variants on the same endpoint
client = boto3.client("sagemaker")
client.update_endpoint_weights_and_capacities(
    EndpointName="my-classifier",
    DesiredWeightsAndCapacities=[
        {"VariantName": "v1", "DesiredWeight": 9.0, "DesiredInstanceCount": 3},
        {"VariantName": "v2", "DesiredWeight": 1.0, "DesiredInstanceCount": 1},
    ],
)
```

Pair with CloudWatch alarms on `Invocations4xxErrors` for the v2 variant; if >1% over 5 min, an EventBridge rule rolls weights back to 100/0.

**Real-world.** Standard production ML release pattern. Always deploy new models behind a traffic split before full rollout. Couples with shadow deploys (which don't return v2's response) for *silent* validation.

**Follow-ups.** Multi-armed bandit instead of fixed split. Shadow + canary in sequence. Feature flag–gated routing for per-user rollout.

---

### Problem 31 — Batch inference on 100M rows

**Statement.** Score 100M user rows nightly through an existing model. Don't pay for an always-on endpoint.

**Solution (three viable patterns).**

1. **SageMaker Batch Transform** — submit; reads from S3, writes to S3, terminates.
2. **Vertex AI Batch Prediction** — submit; reads from GCS or BQ, writes to GCS or BQ.
3. **BQML / inference in BigQuery** — if the model fits BQML or can be imported (Module 5).

Sketch (SageMaker):
```python
transformer = sagemaker.transformer.Transformer(
    model_name="my-classifier",
    instance_count=4,
    instance_type="ml.c5.4xlarge",
    output_path="s3://myorg-scores/2026-04-27/",
    accept="application/json",
    strategy="MultiRecord",
)
transformer.transform(
    data="s3://myorg-features/2026-04-27/",
    content_type="application/x-parquet",
    split_type="Line",
)
transformer.wait()
```

**Real-world.** Most "ML at scale" today is batch, not real-time. Batch jobs that auto-terminate are dramatically cheaper than always-on endpoints.

**Follow-ups.** Spot instances (AWS Batch with Spot). DAG orchestration with Airflow / Argo / Vertex Pipelines. Late-arriving data handling.

---

### Problem 32 — Serve an open-source LLM on GPU efficiently

**Statement.** Self-host Llama or similar on a GPU instance with high throughput.

**Architecture (high level).**

- **Inference server:** vLLM, TGI (Text Generation Inference), or TensorRT-LLM. **vLLM** is the default for Llama-class models in 2026 (PagedAttention; 5–10× tps over naive HF).
- **Container:** prebuilt image (`vllm/vllm-openai:latest` exposes an OpenAI-compatible HTTP API).
- **Compute:** L4 / L40S / A10 / A100 / H100 depending on model size and budget.
- **Networking:** internal LB (only your apps call it).

```bash
docker run --gpus all --shm-size 1g -p 8000:8000 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  vllm/vllm-openai:latest \
  --model meta-llama/Meta-Llama-3.1-8B-Instruct \
  --tensor-parallel-size 1 \
  --max-model-len 8192
```

Now your app calls it like the OpenAI API:
```python
from openai import OpenAI
client = OpenAI(base_url="http://internal-vllm:8000/v1", api_key="dummy")
resp = client.chat.completions.create(
    model="meta-llama/Meta-Llama-3.1-8B-Instruct",
    messages=[{"role":"user","content":"Hello"}],
)
```

**Real-world.** Self-hosted inference makes sense when: you have steady high traffic; you have compliance constraints; or you fine-tune. For variable / lower traffic, third-party APIs are cheaper. Module 10 covers vLLM in depth.

**Follow-ups.** Multi-replica with continuous batching. Speculative decoding. Quantization (AWQ, GPTQ) to fit bigger models on smaller cards.

---

### Problem 33 — Pick the right GPU for serving

**Statement.** Choose a GPU for serving an 8B-parameter LLM at 100 RPS.

**Decision factors:**
- **VRAM:** model + KV cache + batch context. 8B fp16 ≈ 16 GB; in INT8/AWQ ≈ 8-10 GB.
- **TFLOPS / memory bandwidth:** dictates tokens/second.
- **Cost per token:** measure once you have a model running.

For an 8B model:
- **L4 (24GB)** — cheap, fits easily, modest tps. \$0.80/hr (rough).
- **A10G (24GB)** — common, balanced. \$1/hr.
- **L40S (48GB)** — bigger batches, more tps. \$2/hr.
- **A100 40GB** — overkill on memory but fast. \$3/hr.

For a 70B model: A100 80GB or H100; usually with tensor parallelism across 2-4 cards.

**The benchmark you must run:** measure tokens/sec at your actual batch size and sequence length on your candidate hardware. Vendor numbers don't reflect your workload.

**Real-world.** "We picked H100 because it's the best" → 3× the price for 1.2× the throughput on your workload. Always benchmark.

**Follow-ups.** Spot GPU pricing. Reserved instances on Lambda Labs / CoreWeave for steady workloads.

---

### Problem 34 — Auto-shutdown idle GPU instances

**Statement.** Engineers leave dev GPU notebooks running overnight. Cap the bleeding.

**Solution (one of many).**

```bash
# AWS — CloudWatch alarm on low GPU utilization for 30 min, auto-stop
aws cloudwatch put-metric-alarm \
  --alarm-name "idle-gpu-i-abc123" \
  --metric-name GPUUtilization \
  --namespace AWS/EC2 \
  --statistic Average --period 60 --evaluation-periods 30 \
  --threshold 5 --comparison-operator LessThanThreshold \
  --dimensions Name=InstanceId,Value=i-abc123 \
  --alarm-actions arn:aws:automate:us-east-1:ec2:stop
```

For SageMaker / Vertex notebooks: built-in idle shutdown settings — use them.

For ad-hoc instances: tag with `auto-stop=true` and a Lambda runs hourly to stop tagged instances over X hours old or under Y% utilization.

**Real-world.** A single 8×H100 instance left running over a 3-day weekend ≈ \$2,000 wasted. This is the highest-ROI ops chore.

**Follow-ups.** Per-engineer monthly GPU budget alerts. "Hibernate" instead of stop (faster restart, retains EBS state).

---

### Problem 35 — Tag everything; budget every account

**Statement.** Cost dashboard says "Compute: \$50k/month" with no breakdown.

**Solution.**

1. **Mandatory tags.** Adopt a tag policy across the org:
   - `app` (which service)
   - `env` (prod/staging/dev)
   - `team` (who owns it)
   - `cost-center` (for chargeback)

```hcl
provider "aws" {
  region = "us-east-1"
  default_tags {
    tags = {
      app         = var.app_name
      env         = var.env
      team        = var.team
      cost_center = var.cost_center
      managed_by  = "terraform"
    }
  }
}
```

Plus a **tag policy / SCP** that denies resource creation without these tags.

2. **Budgets per account/service** via AWS Budgets / GCP Budgets / Azure Cost Management:
```hcl
resource "aws_budgets_budget" "monthly" {
  name              = "monthly-${var.env}"
  budget_type       = "COST"
  limit_amount      = "1000"
  limit_unit        = "USD"
  time_period_start = "2026-01-01_00:00"
  time_unit         = "MONTHLY"

  notification {
    comparison_operator = "GREATER_THAN"
    threshold           = 80
    threshold_type      = "PERCENTAGE"
    notification_type   = "ACTUAL"
    subscriber_email_addresses = ["finops@myorg.com"]
  }
}
```

3. **Weekly review** of top movers in Cost Explorer / GCP Billing — investigate any service jumping >20%.

**Real-world.** This is how you find unexpected costs (`Cost Center=unknown` is the smoking gun).

**Follow-ups.** Showback / chargeback — use tag-attributed cost to bill teams internally. AWS Cost Anomaly Detection.

---

### Problem 36 — Buy commitments after data, not before

**Statement.** AWS sales is offering a 30% Savings Plan for 3 years. Should you sign?

**Decision framework.**

1. Look at 3 months of stable on-demand spend.
2. Buy commitments only for the **floor** of usage (the minimum you'll always hit). Leave headroom for growth.
3. Mixed strategy: 60-70% reserved/saved, 30-40% on-demand for flexibility, plus Spot for everything that tolerates interruption.
4. Re-evaluate every 6 months; commitments aren't transferable across regions or service families easily.

```python
# AWS — check current Savings Plans coverage
import boto3
ce = boto3.client("ce")
result = ce.get_savings_plans_coverage(
    TimePeriod={"Start": "2026-04-01", "End": "2026-05-01"},
    Granularity="MONTHLY",
)
print(result["SavingsPlansCoverages"])
```

**Real-world.** Premature commitments are the most common FinOps mistake — teams lock in 3-year RIs based on a spike, then traffic drops. Conservative commitments + generous Spot consumption usually beats aggressive Reserved.

**Follow-ups.** Compute Savings Plans (most flexible) vs Reserved Instances (most discount, least flexible). Convertible RIs. Marketplace for selling unused RIs (regions allow this).

---

## 16. Three mini-projects

### Mini-project A — End-to-end FastAPI deploy on AWS
Take the Module 4 e-commerce API. Add: ECR for images, RDS Postgres (multi-AZ), Secrets Manager for the DB URL, an ALB with HTTPS (ACM cert), ECS Fargate service in private subnets, GitHub Actions OIDC pipeline that builds + deploys on merge to main, alarms on 5xx error rate, CloudWatch dashboard. Document RTO/RPO and run a chaos drill (kill a task; confirm the LB drains).

**Skills exercised:** every section. Counts as your AWS deploy reference.

### Mini-project B — Same on GCP, with Cloud Run + Cloud SQL
Repeat Mini-A on GCP. Differences to wrestle with: Cloud Run's concurrency model, Cloud SQL Auth Proxy, Workload Identity Federation for GitHub. Compare developer experience, deploy speed, and cost between the two clouds.

**Skills exercised:** managed containers, GCP IAM, Cloud Run scaling.

### Mini-project C — Self-hosted vLLM behind FastAPI
Provision an L4 or L40S GPU VM. Run vLLM with an open-weight 7B/8B model. Front it with a FastAPI service that adds: API-key auth, per-user rate limiting (Module 4 Problem 10), token-stream forwarding via SSE, request logging with cost-per-call. Track GPU utilization and tokens/sec; right-size the GPU.

**Skills exercised:** GPU provisioning, container deploy, observability, cost reasoning.

---

## 17. Real-world usage map

| Concept | Where it returns later |
|---|---|
| Workload identity / IRSA | Every ML/LLM serving service in Modules 7+ |
| S3 / GCS for model artifacts | Module 7, 12 (MLOps registries) |
| Presigned URLs | Module 4 (uploads) — extends to dataset ingestion in Module 12 |
| Containerized deploy | Module 7+ — every model behind a FastAPI surface |
| Cloud Run / App Runner | Cheapest serving option for low-traffic ML APIs |
| K8s + GPUs | Self-hosted LLM serving (Modules 10, 13) |
| Secrets Manager / Key Vault | LLM API keys, DB creds throughout |
| OpenTelemetry | LLM observability (Module 13 — langfuse / Phoenix bridges) |
| Spot / preemptible | Training and batch jobs in Modules 7-8 |
| GPU instances | Modules 8-10 (DL, NLP/CV, LLMs) |
| Vertex AI / SageMaker / Azure ML | Module 12 — managed model lifecycle |
| Budget alerts | Module 13 — LLM token-cost guardrails |
| VPC endpoints | Module 12 — keeping ML traffic on the cloud backbone |

---

## 18. Interview pitfalls — what NOT to say

- **"I'd put my AWS keys in env vars."** Use IAM roles / OIDC. Static keys are a red flag.
- **"Public S3 bucket so the frontend can read it."** Use CloudFront in front + signed URLs / bucket policies. Never raw public.
- **"I'd use Kubernetes for this single service."** Defend the choice. For most apps, managed containers are simpler and cheaper.
- **"The default VPC is fine."** For prod, define your own. Talk about subnets and NAT cost.
- **"I'll use the `:latest` tag in production."** Immutable tags only.
- **"We don't need a CI gate to prod."** Manual approval / canary is the floor.
- **"I'll add monitoring later."** Day 1 / Module 4 — this is non-negotiable for prod services.
- **"Multi-region from day one."** Multi-AZ from day one. Multi-region only when the business case is real (cost is significant).
- **"Cost is finance's problem."** It's everyone's problem. Engineers create most of the bill.
- **"GPUs are too expensive."** Maybe — but Spot + scale-to-zero + right-sizing change the equation by 5-10×. Show the math.
- **"I'll reach for SageMaker / Vertex AI for everything."** Often overkill. A FastAPI in a container is fine for many models.
- **"`*` in IAM policy because we're in dev."** Dev habits become prod habits. Practice least-privilege everywhere.

**How to communicate.** When given a "design a cloud deploy" question, narrate (1) compute target choice + reason, (2) identity model (workload identity, no static keys), (3) networking (private subnets for app, internal LB for service-to-service), (4) secrets path, (5) deploy strategy (rolling vs canary), (6) observability (logs/metrics/traces/alerts), (7) cost guard rails (tags, budgets), (8) DR posture (RTO/RPO).

---

## 19. Cheatsheet

```text
THE THREE-CLOUD MAP
  Identity:    IAM Role | Service Account | Managed Identity
  Storage:     S3 | GCS | Blob
  Container:   ECS / App Runner | Cloud Run | Container Apps
  K8s:         EKS | GKE | AKS
  Secret:      Secrets Manager | Secret Manager | Key Vault
  DNS:         Route 53 | Cloud DNS | Azure DNS
  ML:          SageMaker | Vertex AI | Azure ML

IDENTITY (do)
  workload identity (instance role / SA / Managed Identity) — NO static keys
  GitHub Actions -> AWS via OIDC (id-token: write + assume-role)
  EKS pods: IRSA  | GKE: Workload Identity  | AKS: Workload Identity
  Block public S3/GCS/Blob at org/account level
  Separate accounts/projects per env (dev/stage/prod)

IAM POLICY HABITS
  least-privilege; specify resource ARN; use conditions (StringLike, ArnEquals)
  Access Analyzer / Policy Recommender to shrink *
  permissions boundary as a cap on roles; SCP as org-wide guardrails
  resource policies + identity policies must BOTH allow

NETWORKING
  VPC -> public subnets (LB) + private subnets (app, DB)
  Security Groups: source by SG reference, not IP
  VPC endpoint (gateway) for S3/DynamoDB — free, skips NAT
  PrivateLink / interface endpoints for other services
  Internal LB for service-to-service; never expose to internet by accident
  app must bind 0.0.0.0, not 127.0.0.1

OBJECT STORAGE
  versioning ON for models / important data
  lifecycle: STANDARD -> IA (30d) -> Glacier (90d) -> delete (Nyrs)
  presigned URLs for direct client upload/download
  KMS for sensitive data; CMK for full control
  abort incomplete multipart uploads (lifecycle rule)

COMPUTE DECISION
  HTTP service, low ops, scale 0..N: Cloud Run / App Runner / Container Apps
  Multi-service, advanced needs: EKS/GKE/AKS
  Event-driven glue: Lambda / Functions
  Long GPU jobs: spot VM with checkpointing, OR Batch / SageMaker / Vertex
  Persistent GPU serving: SageMaker / Vertex endpoints, OR managed K8s + GPU pool

CONTAINERS
  multi-stage Dockerfile; slim base; USER 1000; .dockerignore
  pin base image digest; tag with git SHA, never :latest in prod
  HEALTHCHECK + readiness/liveness probes
  graceful shutdown: SIGTERM handler + LB drain (preStop sleep)

K8s (the survival vocabulary)
  Pod | Deployment | Service | Ingress
  ConfigMap | Secret | ServiceAccount
  HPA (CPU) | KEDA (custom metric)
  Namespace | NetworkPolicy | PodDisruptionBudget
  kubectl: apply | rollout | logs | exec | describe | port-forward

SECRETS
  cloud secret store -> orchestrator injection -> env var
  IAM auth to RDS / Cloud SQL when possible (no DB password)
  rotate via Secrets Manager rotation function
  cache in app (5-min TTL) for hot reads
  NEVER: in code, in image layers, in env values committed

OBSERVABILITY (the four golden signals)
  latency (p50/p95/p99) | traffic (RPS) | errors | saturation
  structured JSON logs to stdout (cloud collects)
  Prometheus /metrics; Grafana / managed Prometheus
  OpenTelemetry traces; OTLP collector; cloud or 3rd-party backend
  alerts on user symptoms, not server CPU

CI/CD
  PR: lint + types + tests + image scan
  main: build, push to registry with git SHA
  staging deploy: auto on merge
  prod deploy: gated approval + canary
  migrations: before app deploy, backward-compatible
  OIDC, not static keys; least-priv role for the deployer

COST CONTROLS
  tags: app, env, team, cost-center (mandatory)
  budgets per account/project, alerts at 50/80/100%
  Spot/preemptible for training + batch
  scale-to-zero for low-traffic services
  GPU auto-stop on idle; Lifecycle policies on object storage
  VPC endpoints to skip NAT charges
  Commit (RI / Savings Plan) only after 3 months of stable usage

ML SERVING
  light traffic: FastAPI in Cloud Run / App Runner
  managed lifecycle: SageMaker / Vertex AI / Azure ML
  self-host LLM: vLLM / TGI on GPU VM or K8s
  batch inference: SageMaker Batch / Vertex Batch / Spark / BQML
  always: model registry + versioning + traffic split for new versions

GPUs
  T4 < L4 < A10/A10G < L40S < A100 < H100 < H200/B200
  benchmark with YOUR workload; vendor numbers lie
  use cloud DL containers (driver+CUDA+framework pre-installed)
  spot/preemptible 60-90% off; checkpoint to S3 every N minutes
  request quota a week ahead

ANTI-PATTERNS
  static keys; * IAM; public S3; root in container; :latest tag
  single-AZ DB; no monitoring; no budget alerts; manual infra
  K8s for one service; GPU instances left on; no tags
  egress over public internet (use endpoints); RTO/RPO undefined
```

---

## 20. Prerequisites & next steps

**Prerequisites covered? You can:**
- Pick the right compute for an ML/LLM service (managed container vs K8s vs serverless vs VM).
- Set up workload identity so your code never sees static credentials.
- Write a least-privilege IAM policy and shrink an over-broad one with Access Analyzer.
- Build a small, secure Dockerfile and deploy it via CI/CD with OIDC.
- Plan a VPC with public/private subnets, security groups, and VPC endpoints.
- Store and inject secrets without touching git or env-var files.
- Wire up logs, metrics, traces, and alerts before first deploy.
- Estimate the cost of a workload, set budgets and tags, and use Spot/scale-to-zero appropriately.
- Deploy a model behind SageMaker / Vertex AI / a self-hosted vLLM — and pick between them.
- Provision GPUs with the right card class for the workload.

**Next steps in the bible:**
- **Module 7 — Classical ML.** First time you put a real model in a FastAPI service running in a container in the cloud.
- **Module 8 — Deep learning.** GPU usage, training jobs, larger artifacts.
- **Module 12 — MLOps.** Model registry, lineage, training pipelines, monitoring.
- **Module 13 — LLMOps.** Cost tracking, prompt management, observability for LLM apps.

**External study (if you want depth):**
- *AWS Well-Architected Framework*, *GCP Architecture Framework*, *Azure Well-Architected* — vendor-published, opinionated, free; read the operational excellence + reliability + cost optimization pillars.
- *The DevOps Handbook* — Module 6 in book form.
- *Site Reliability Engineering* (Google's SRE book, free online) — the operational mental model.
- *FinOps for Engineers* — the cost-optimization side of the house, increasingly its own discipline.

---

*End of Module 6. Module 7 covers Classical ML — scikit-learn, XGBoost, LightGBM, feature engineering, hyperparameter tuning, model interpretation — same structure, 35+ problems.*
