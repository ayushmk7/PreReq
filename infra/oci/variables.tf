variable "tenancy_ocid" {
  description = "OCI tenancy OCID"
  type        = string
}

variable "user_ocid" {
  description = "OCI user OCID"
  type        = string
}

variable "fingerprint" {
  description = "API key fingerprint"
  type        = string
}

variable "private_key_path" {
  description = "Path to OCI API private key"
  type        = string
}

variable "region" {
  description = "OCI region"
  type        = string
}

variable "compartment_ocid" {
  description = "Target compartment for prereq-dev resources"
  type        = string
}

variable "project_prefix" {
  description = "Name prefix for OCI resources"
  type        = string
  default     = "prereq-dev"
}

variable "vcn_cidr" {
  description = "VCN CIDR block"
  type        = string
  default     = "10.20.0.0/16"
}

variable "public_subnet_cidr" {
  description = "Public subnet CIDR"
  type        = string
  default     = "10.20.1.0/24"
}

variable "app_subnet_cidr" {
  description = "Private app subnet CIDR"
  type        = string
  default     = "10.20.2.0/24"
}

variable "db_subnet_cidr" {
  description = "Private DB subnet CIDR"
  type        = string
  default     = "10.20.3.0/24"
}

variable "bucket_names" {
  description = "Object storage buckets required by the app"
  type        = list(string)
  default     = ["frontend-static", "uploads", "exports", "backups"]
}

variable "ocir_repositories" {
  description = "OCIR repository names"
  type        = list(string)
  default     = ["prereq-api", "prereq-worker"]
}

variable "create_alarm_placeholders" {
  description = "Create monitoring alarm placeholders"
  type        = bool
  default     = true
}
