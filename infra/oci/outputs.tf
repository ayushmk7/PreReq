output "vcn_id" {
  value = oci_core_vcn.main.id
}

output "public_subnet_id" {
  value = oci_core_subnet.public_lb.id
}

output "private_app_subnet_id" {
  value = oci_core_subnet.private_app.id
}

output "private_db_subnet_id" {
  value = oci_core_subnet.private_db.id
}

output "object_storage_namespace" {
  value = data.oci_objectstorage_namespace.ns.namespace
}

output "bucket_names" {
  value = [for b in oci_objectstorage_bucket.buckets : b.name]
}

output "ocir_repositories" {
  value = [for r in oci_artifacts_container_repository.repos : r.display_name]
}
