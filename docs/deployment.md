# Deployment Guide

## Overview

Genesis can be deployed using Docker, Docker Compose, or Kubernetes. This guide covers all deployment methods.

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+ (for local deployment)
- Kubernetes 1.27+ (for production deployment)
- Helm 3.0+ (for Kubernetes)
- Terraform 1.0+ (for infrastructure)

## Local Development

### Using Docker

```bash
# Build image
docker build -t genesis:latest .

# Run container
docker run -it --rm \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/src:/app/src \
  genesis:latest genesis run
```

### Using Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f genesis

# Stop services
docker-compose down
```

Services included:
- `genesis`: Main application
- `genesis-loop`: Autonomous loop
- `redis`: Caching
- `postgres`: Database

## Kubernetes Deployment

### Prerequisites

1. **Create cluster** (if needed):
```bash
# AWS EKS
aws eks create-cluster --name genesis-cluster

# Or use Terraform
cd infra/terraform
terraform init
terraform apply
```

2. **Configure kubectl**:
```bash
aws eks update-kubeconfig --name genesis-cluster
```

### Using Helm

1. **Install chart**:
```bash
# Install from local chart
helm install genesis ./infra/helm/genesis

# Or with custom values
helm install genesis ./infra/helm/genesis \
  -f custom-values.yaml
```

2. **Verify deployment**:
```bash
# Check pods
kubectl get pods -l app=genesis

# Check services
kubectl get svc -l app=genesis

# View logs
kubectl logs -l app=genesis -f
```

3. **Upgrade**:
```bash
helm upgrade genesis ./infra/helm/genesis
```

4. **Uninstall**:
```bash
helm uninstall genesis
```

### Using kubectl Directly

```bash
# Apply manifests
kubectl apply -f infra/kubernetes/

# Check status
kubectl rollout status deployment/genesis

# Scale
kubectl scale deployment/genesis --replicas=5
```

## Configuration

### Environment Variables

```bash
GENESIS_ENV=production          # Environment (dev, staging, prod)
LOG_LEVEL=INFO                  # Logging level
GENESIS_TARGET_THRESHOLD=1.2    # Performance threshold
GENESIS_LOOP_INTERVAL=6h        # Loop interval
```

### Helm Values

```yaml
# custom-values.yaml
replicaCount: 5

resources:
  limits:
    cpu: 2000m
    memory: 4Gi
  requests:
    cpu: 1000m
    memory: 2Gi

genesis:
  environment: production
  targetThreshold: 1.2
  logLevel: INFO

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 20
```

## Infrastructure as Code

### Terraform

1. **Initialize**:
```bash
cd infra/terraform
terraform init
```

2. **Plan**:
```bash
terraform plan \
  -var="environment=prod" \
  -var="cluster_name=genesis-prod"
```

3. **Apply**:
```bash
terraform apply \
  -var="environment=prod"
```

4. **Outputs**:
```bash
terraform output cluster_endpoint
terraform output db_endpoint
```

### Resources Created

- EKS Cluster with node groups
- VPC with public/private subnets
- RDS PostgreSQL database
- ElastiCache Redis cluster
- Security groups
- IAM roles

## Monitoring

### Health Checks

```bash
# Kubernetes
kubectl get pods
kubectl describe pod <pod-name>

# Docker
docker ps
docker inspect <container-id>
```

### Logs

```bash
# Kubernetes
kubectl logs -l app=genesis -f
kubectl logs <pod-name> --previous

# Docker
docker logs genesis -f
```

### Metrics

```bash
# Kubernetes
kubectl top pods
kubectl top nodes

# Docker
docker stats
```

## Scaling

### Horizontal Pod Autoscaling

```yaml
autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 20
  targetCPUUtilizationPercentage: 80
  targetMemoryUtilizationPercentage: 80
```

### Manual Scaling

```bash
# Kubernetes
kubectl scale deployment/genesis --replicas=10

# Docker Compose
docker-compose up --scale genesis=5
```

## High Availability

### Multi-Zone Deployment

```yaml
affinity:
  podAntiAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
    - labelSelector:
        matchExpressions:
        - key: app
          operator: In
          values:
          - genesis
      topologyKey: topology.kubernetes.io/zone
```

### Database Replication

- RDS Multi-AZ for PostgreSQL
- Redis with replicas
- Automated backups

## Security

### Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: genesis-network-policy
spec:
  podSelector:
    matchLabels:
      app: genesis
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: genesis
```

### Secrets Management

```bash
# Create secret
kubectl create secret generic genesis-secrets \
  --from-literal=db-password=secret \
  --from-literal=redis-password=secret

# Use in deployment
env:
- name: DB_PASSWORD
  valueFrom:
    secretKeyRef:
      name: genesis-secrets
      key: db-password
```

### Pod Security

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 1000
  capabilities:
    drop:
    - ALL
  readOnlyRootFilesystem: true
```

## Canary Deployments

### Using Flagger

```yaml
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: genesis
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: genesis
  progressDeadlineSeconds: 60
  service:
    port: 8080
  analysis:
    interval: 1m
    threshold: 10
    maxWeight: 50
    stepWeight: 5
    metrics:
    - name: request-success-rate
      thresholdRange:
        min: 99
```

## Rollback

### Kubernetes

```bash
# View history
kubectl rollout history deployment/genesis

# Rollback to previous
kubectl rollout undo deployment/genesis

# Rollback to specific revision
kubectl rollout undo deployment/genesis --to-revision=2
```

### Helm

```bash
# View history
helm history genesis

# Rollback
helm rollback genesis 1
```

## Backup and Restore

### Database

```bash
# Backup
pg_dump -h <db-host> -U genesis genesis > backup.sql

# Restore
psql -h <db-host> -U genesis genesis < backup.sql
```

### Application Data

```bash
# Backup PVCs
kubectl get pvc
kubectl exec <pod> -- tar czf - /app/data > backup.tar.gz

# Restore
kubectl exec <pod> -- tar xzf - -C /app/data < backup.tar.gz
```

## Troubleshooting

### Pod not starting

```bash
kubectl describe pod <pod-name>
kubectl logs <pod-name>
kubectl get events
```

### Out of resources

```bash
kubectl top nodes
kubectl describe node <node-name>
kubectl get pods --all-namespaces
```

### Network issues

```bash
kubectl exec <pod-name> -- ping <service-name>
kubectl get svc
kubectl describe svc <service-name>
```

## Production Checklist

- [ ] Resource limits configured
- [ ] Health checks implemented
- [ ] Monitoring enabled
- [ ] Logging configured
- [ ] Backups automated
- [ ] Security policies applied
- [ ] Secrets encrypted
- [ ] Scaling configured
- [ ] High availability setup
- [ ] Disaster recovery plan
- [ ] Documentation complete
- [ ] Runbooks created
