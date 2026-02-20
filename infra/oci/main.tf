data "oci_objectstorage_namespace" "ns" {
  compartment_id = var.compartment_ocid
}

resource "oci_core_vcn" "main" {
  compartment_id = var.compartment_ocid
  cidr_blocks    = [var.vcn_cidr]
  display_name   = "${var.project_prefix}-vcn"
  dns_label      = "prereqvcn"
}

resource "oci_core_internet_gateway" "igw" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.main.id
  display_name   = "${var.project_prefix}-igw"
}

resource "oci_core_nat_gateway" "nat" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.main.id
  display_name   = "${var.project_prefix}-nat"
}

resource "oci_core_route_table" "public_rt" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.main.id
  display_name   = "${var.project_prefix}-public-rt"

  route_rules {
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_internet_gateway.igw.id
  }
}

resource "oci_core_route_table" "private_rt" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.main.id
  display_name   = "${var.project_prefix}-private-rt"

  route_rules {
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_nat_gateway.nat.id
  }
}

resource "oci_core_subnet" "public_lb" {
  compartment_id    = var.compartment_ocid
  vcn_id            = oci_core_vcn.main.id
  cidr_block        = var.public_subnet_cidr
  display_name      = "${var.project_prefix}-public-lb"
  route_table_id    = oci_core_route_table.public_rt.id
  prohibit_public_ip_on_vnic = false
  dns_label         = "publiclb"
}

resource "oci_core_subnet" "private_app" {
  compartment_id    = var.compartment_ocid
  vcn_id            = oci_core_vcn.main.id
  cidr_block        = var.app_subnet_cidr
  display_name      = "${var.project_prefix}-private-app"
  route_table_id    = oci_core_route_table.private_rt.id
  prohibit_public_ip_on_vnic = true
  dns_label         = "privateapp"
}

resource "oci_core_subnet" "private_db" {
  compartment_id    = var.compartment_ocid
  vcn_id            = oci_core_vcn.main.id
  cidr_block        = var.db_subnet_cidr
  display_name      = "${var.project_prefix}-private-db"
  route_table_id    = oci_core_route_table.private_rt.id
  prohibit_public_ip_on_vnic = true
  dns_label         = "privatedb"
}

resource "oci_core_network_security_group" "api_nsg" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.main.id
  display_name   = "${var.project_prefix}-api-nsg"
}

resource "oci_core_network_security_group" "db_nsg" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.main.id
  display_name   = "${var.project_prefix}-db-nsg"
}

resource "oci_core_network_security_group_security_rule" "api_ingress_from_lb" {
  network_security_group_id = oci_core_network_security_group.api_nsg.id
  direction                 = "INGRESS"
  protocol                  = "6"
  source                    = var.public_subnet_cidr
  source_type               = "CIDR_BLOCK"

  tcp_options {
    destination_port_range {
      min = 8000
      max = 8000
    }
  }
}

resource "oci_core_network_security_group_security_rule" "db_ingress_from_app" {
  network_security_group_id = oci_core_network_security_group.db_nsg.id
  direction                 = "INGRESS"
  protocol                  = "6"
  source                    = var.app_subnet_cidr
  source_type               = "CIDR_BLOCK"

  tcp_options {
    destination_port_range {
      min = 5432
      max = 5432
    }
  }
}

resource "oci_objectstorage_bucket" "buckets" {
  for_each       = toset(var.bucket_names)
  compartment_id = var.compartment_ocid
  namespace      = data.oci_objectstorage_namespace.ns.namespace
  name           = "${var.project_prefix}-${each.value}"
  storage_tier   = "Standard"
}

resource "oci_artifacts_container_repository" "repos" {
  for_each       = toset(var.ocir_repositories)
  compartment_id = var.compartment_ocid
  display_name   = "${var.project_prefix}/${each.value}"
  is_immutable   = false
  is_public      = false
}

# Alarm placeholders. Update query dimensions to match final resources.
resource "oci_monitoring_alarm" "api_5xx_placeholder" {
  count               = var.create_alarm_placeholders ? 1 : 0
  compartment_id      = var.compartment_ocid
  destinations        = []
  display_name        = "${var.project_prefix}-api-5xx-placeholder"
  is_enabled          = false
  metric_compartment_id = var.compartment_ocid
  namespace           = "oci_lbaas"
  query               = "HttpCode_Backend_5xx[1m].sum() > 5"
  severity            = "CRITICAL"
  body                = "Placeholder alarm. Wire destinations and dimensions before enabling."
  pending_duration    = "PT1M"
}

resource "oci_monitoring_alarm" "latency_placeholder" {
  count               = var.create_alarm_placeholders ? 1 : 0
  compartment_id      = var.compartment_ocid
  destinations        = []
  display_name        = "${var.project_prefix}-latency-placeholder"
  is_enabled          = false
  metric_compartment_id = var.compartment_ocid
  namespace           = "oci_lbaas"
  query               = "BackendConnectionTime[1m].percentile(0.95) > 1000"
  severity            = "WARNING"
  body                = "Placeholder alarm. Wire destinations and dimensions before enabling."
  pending_duration    = "PT5M"
}
