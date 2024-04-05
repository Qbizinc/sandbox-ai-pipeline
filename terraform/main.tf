terraform {
  required_providers {
    google = {
      source = "hashicorp/google"
      version = "5.23.0"
    }
  }
}

provider "google" {
  credentials = file("")
  project     = ""
  region      = ""
}

resource "google_sql_database_instance" "vector" {
  name             = "postgres-vectordb"
  database_version = "POSTGRES_15"
  region           = ""
  project          = ""
  deletion_protection = false

  settings {
    tier            = "db-f1-micro"
    edition = "ENTERPRISE"
    availability_type = "ZONAL"
    disk_type = "PD_SSD"
    disk_size = 10
  }
}

resource "google_sql_database" "gdrive" {
  name     = "gdrive-db"
  instance = google_sql_database_instance.vector.name
  project  = ""
}

resource "google_sql_user" "users" {
  name     = "default"
  instance = google_sql_database_instance.vector.name
  password = ""
}

output "connection_name" {
  value = google_sql_database_instance.vector.connection_name
}