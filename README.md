# Sandbox AI Pipeline

## About this Project

First repository draft to build pipelines for AI projects

## Build SQL Database

```sh
cd sandbox-ai-pipeline/terraform
terraform init
terraform plan
terraform apply
```

to destroy database

```sh
cd sandbox-ai-pipeline/terraform
terraform destroy
```

to populate database

```sh
python src/main.py
```

Is required to fill on the main.tf and main.py the following values to execute the code:

- project_id
- location
- service_account_json_path
- client_secrets_file (for Oauth Google Drive authorization)
- password for default user