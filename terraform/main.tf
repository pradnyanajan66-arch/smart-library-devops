terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "ap-south-1"
}

data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_vpc" "student_vpc" {
  cidr_block           = "10.1.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name    = "unit4-student-vpc"
    Project = "Unit4StudentPlatform"
  }
}

resource "aws_subnet" "public_subnet" {
  vpc_id                  = aws_vpc.student_vpc.id
  cidr_block              = "10.1.1.0/24"
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true

  tags = {
    Name    = "unit4-public-subnet"
    Project = "Unit4StudentPlatform"
  }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.student_vpc.id

  tags = {
    Name = "unit4-igw"
  }
}

resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.student_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }

  tags = {
    Name = "unit4-public-route-table"
  }
}

resource "aws_route_table_association" "public_assoc" {
  subnet_id      = aws_subnet.public_subnet.id
  route_table_id = aws_route_table.public_rt.id
}

resource "aws_security_group" "student_sg" {
  name        = "unit4-student-platform-sg"
  description = "Security group for Unit 4 student platform"
  vpc_id      = aws_vpc.student_vpc.id

  ingress {
    description = "SSH from my public IP"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["98.89.35.185/32"]
  }

  ingress {
    description = "HTTP for web application"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Student API direct access from my public IP"
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["98.89.35.185/32"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "unit4-student-platform-sg"
    Project = "Unit4StudentPlatform"
  }
}

resource "aws_s3_bucket" "student_data" {
  bucket_prefix = "unit4-student-data-"

  tags = {
    Name    = "unit4-student-data"
    Project = "Unit4StudentPlatform"
  }
}

resource "aws_s3_bucket_public_access_block" "student_data" {
  bucket                  = aws_s3_bucket.student_data.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "student_data" {
  bucket = aws_s3_bucket.student_data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_versioning" "student_data" {
  bucket = aws_s3_bucket.student_data.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_instance" "student_app" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = "t3.micro"
  subnet_id                   = aws_subnet.public_subnet.id
  vpc_security_group_ids      = [aws_security_group.student_sg.id]
  associate_public_ip_address = true

  root_block_device {
    volume_size = 8
    volume_type = "gp3"
    encrypted   = true
  }

  tags = {
    Name    = "unit4-student-app"
    Project = "Unit4StudentPlatform"
  }
}

output "vpc_id" {
  value = aws_vpc.student_vpc.id
}

output "public_subnet_id" {
  value = aws_subnet.public_subnet.id
}

output "security_group_id" {
  value = aws_security_group.student_sg.id
}

output "s3_bucket_name" {
  value = aws_s3_bucket.student_data.bucket
}

output "app_public_ip" {
  value = aws_instance.student_app.public_ip
}
