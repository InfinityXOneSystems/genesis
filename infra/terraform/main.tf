# Terraform configuration for Genesis infrastructure

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  backend "s3" {
    bucket = "genesis-terraform-state"
    key    = "genesis/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
}

# Variables
variable "aws_region" {
  description = "AWS region"
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  default     = "dev"
}

variable "cluster_name" {
  description = "EKS cluster name"
  default     = "genesis-cluster"
}

# VPC
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"
  
  name = "${var.cluster_name}-vpc"
  cidr = "10.0.0.0/16"
  
  azs             = ["${var.aws_region}a", "${var.aws_region}b", "${var.aws_region}c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
  
  enable_nat_gateway = true
  enable_vpn_gateway = false
  
  tags = {
    Environment = var.environment
    Project     = "genesis"
  }
}

# EKS Cluster
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"
  
  cluster_name    = var.cluster_name
  cluster_version = "1.27"
  
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets
  
  eks_managed_node_groups = {
    genesis = {
      min_size     = 2
      max_size     = 10
      desired_size = 3
      
      instance_types = ["t3.large"]
      capacity_type  = "ON_DEMAND"
    }
  }
  
  tags = {
    Environment = var.environment
    Project     = "genesis"
  }
}

# RDS for persistent storage
resource "aws_db_instance" "genesis" {
  identifier        = "genesis-db"
  engine            = "postgres"
  engine_version    = "15.3"
  instance_class    = "db.t3.medium"
  allocated_storage = 20
  
  db_name  = "genesis"
  username = "genesis"
  password = var.db_password
  
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.genesis.name
  
  backup_retention_period = 7
  skip_final_snapshot     = true
  
  tags = {
    Environment = var.environment
    Project     = "genesis"
  }
}

# ElastiCache for Redis
resource "aws_elasticache_cluster" "genesis" {
  cluster_id           = "genesis-cache"
  engine               = "redis"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  engine_version       = "7.0"
  port                 = 6379
  
  security_group_ids = [aws_security_group.redis.id]
  subnet_group_name  = aws_elasticache_subnet_group.genesis.name
  
  tags = {
    Environment = var.environment
    Project     = "genesis"
  }
}

# Security Groups
resource "aws_security_group" "rds" {
  name        = "genesis-rds-sg"
  description = "Security group for Genesis RDS"
  vpc_id      = module.vpc.vpc_id
  
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = module.vpc.private_subnets_cidr_blocks
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "redis" {
  name        = "genesis-redis-sg"
  description = "Security group for Genesis Redis"
  vpc_id      = module.vpc.vpc_id
  
  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = module.vpc.private_subnets_cidr_blocks
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Subnet Groups
resource "aws_db_subnet_group" "genesis" {
  name       = "genesis-db-subnet"
  subnet_ids = module.vpc.private_subnets
}

resource "aws_elasticache_subnet_group" "genesis" {
  name       = "genesis-cache-subnet"
  subnet_ids = module.vpc.private_subnets
}

# Outputs
output "cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "cluster_name" {
  value = module.eks.cluster_name
}

output "db_endpoint" {
  value = aws_db_instance.genesis.endpoint
}

output "redis_endpoint" {
  value = aws_elasticache_cluster.genesis.cache_nodes[0].address
}
