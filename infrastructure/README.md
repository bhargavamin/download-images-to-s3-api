# Deploy infrastructure for Download Image to S3 Bucket Api

- Language: YAML
- Platform: Docker & AWS (ECS, Fargate, Cloudformation, RDS, IAM, VPC and S3)
- Author: Bhargav Amin

Infrastructure is to be deployed in three steps:

1. Deploy AWS Infra
2. Create Database, User and Password
3. Replace variables and secrets
4. Deploy database schema
5. Build & Deploy docker image

## 1. Deploy AWS infrastructure

pre-req:

- AWS Account and Admin access

**Step 1: Deploy `base_infra.yaml`**

```bash
   $ aws cloudformation deploy \
   --template-file cloudformation-templates/infrastructure.yaml \
   --region <region> \
   --stack-name infra-template \
   --capabilities CAPABILITY_NAMED_IAM
```

**Step 2: Deploy `s3_and_rds.yaml`**

```bash
   $ aws cloudformation deploy \
   --template-file cloudformation-templates/s3_and_rds.yaml \
   --region <region> \
   --stack-name s3-rds-template \
   --parameter-overrides ShortEnv=p DatabaseRootPw=admin123 \
   --capabilities CAPABILITY_NAMED_IAM
```

Note: You can also manually upload same template in Cloudformation.

Once this is done you will have a RDS instance running, a S3 bucket created and ECS application created with application load balancer and target group.

**Step 3: Set environment variables for API**

* Set environment varible `ENV` from terminal : `export ENV=development`
* Replace development environment variables in `config.py` file in api directory**

```
   S3_BUCKET = '<bucket name>'
   DB_HOST = '<url of rds instance>'
   DB_USER = '<rds db user>'
   DB_PWD = '<rds db password>'
   DB_PORT = '3306'
   DB_NAME = 'download_images'
   AWS_ACCESS_KEY_ID = '<access key>'
   AWS_SECRET_ACCESS_KEY = '<secret key>'
   AWS_REGION = '<region>'
```

- Copy following values from `s3_and_rds.yaml` template `Outputs`.
      - DatabaseInstanceEndpointAddress
      - ImageBucket
- You will also need to generate `access key` and `secret key` for the IAM User which was automatically create by `s3_and_rds.yaml` template, you can find the username in `Outputs` of the stack.
- For `DB_USER` and `DB_PWD` variables you can use create a database user and password by following the next step.

## 2. Create Database, User and Password

Pre-req:

- Any mysql client to connect to RDS instance
- Python 3 and `pip install -r requirements.txt`

**Create database and user**

Login to RDS instance as `root` user and create a application db user named `appuser`.

- Create database: `CREATE DATABASE download_images;`
- Create user: `GRANT ALL PRIVILEGES ON download_images.* TO 'appuser'@'%' IDENTIFIED BY 'password';`

Once user is successfully created copy the user name and password in `config.py` file under `development` class.

## 4. Run database migrations

pre-req:

- Ensure correct database details are set in `config.py`

From `api` directory run migrations using following command:

1. `python manage.py db init`
2. `python manage.py db migrate`
3. `python manage.py db upgrade`

Once migrations are successfully executed you will see a `download_images` table created under `downloads` database.

Now you have configured all the secrets necessary to build and deploy the application.

## 5. Build and Push Docker image

pre-req:

- AWS CLI configured on system with admin privileges
- Docker and Docker Compose installed

Run script `deploy.py <base_infra,yaml cloudformation stack> <environment>`

For eg. `deploy.py base-infra-stack development`

This script will build docker container locally first, deploy to ECR repo(if doesn't exist it will create one repo) then will create ECS Task Defination and then launch ECS Service with Fargate.

You can check the application and deployment logs from Cloudwatch log group named  `/ecs/image_to_s3_api`.
