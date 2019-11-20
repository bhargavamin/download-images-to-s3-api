import subprocess
import sys
import yaml
import boto3
import base64


# Initialize services
ecs_client = boto3.client('ecs')
ecr_client = boto3.client('ecr')
cfn_client = boto3.client('cloudformation')
elb_client = boto3.client('elbv2')
cw_client = boto3.client('logs')


def check_ecr_repo(service):
    # Check if ECR repo exists
    repo_list = []
    ecr_repos = ecr_client.describe_repositories()
    for repo in ecr_repos['repositories']:
        print
        repo_list.append(repo['repositoryName'])
    if service in repo_list:
        print("Matched!", service)
        return True
    else:
        print("ECR [{}] reposiroty not found!".format(service))
        return False


def fetch_repo_info(service):
    # Fetch ECR repo information
    try:
        output = ecr_client.describe_repositories(repositoryNames=[service])
        print("Fetching info for [{}] ECR repository....".format(service))

        for repo in output['repositories']:
            if repo['repositoryName'] == service:
                print("Name: ", repo['repositoryName'])
                print("URL: ", repo['repositoryUri'])
                repo_uri = repo['repositoryUri']
                break
    except Exception:
        print("Problem fetching info for {} ECR repo".format(service))
    return(repo_uri)


def create_ecr_repo(service):
    # Create ECR repo
    response = input(
        "Do you want to create a new ECR repo named {}"
        "? y or n : ".format(service))
    if response == 'y' or response == 'yes':
        output = ecr_client.create_repository(repositoryName=service)
        print("Created [{}] ECR repository.".format(service))
        print("Name: ", output['repository']['repositoryName'])
        print("URL: ", output['repository']['repositoryUri'])
    else:
        print("Skipping everything.")
        exit(1)
    return


def authenticate_ecr():
    # Authenticate with ECR
    response = ecr_client.get_authorization_token()
    print("Authorizing...")
    for auth in response["authorizationData"]:
        auth_token = base64.b64decode(auth['authorizationToken']).decode()
        username, password = auth_token.split(':')
        try:
            auth_string = "docker login -u {} -p {} {}".format(
                    username, password, auth['proxyEndpoint'])
            subprocess.run([auth_string], check=True, shell=True)
            print("Authentication successfull!")
        except subprocess.CalledProcessError as e:
            print("Authentication Failed!")
            raise RuntimeError(
              "command '{}' return with error"
              "(code {}): {}".format(
                  e.cmd,
                  e.returncode,
                  e.output))


def build_push_image(service, repo_uri):
    # Build Docker images
    compose_file = "docker-compose.yml"
    response = input("Build and Push new Docker Image to ECR? y or n : ")

    if response == 'y' or response == 'yes':
        # Execute "docker-compose build" and abort if it fails.
        subprocess.check_call(["docker-compose", "-f", compose_file, "build"])

        compose_image = "api_{}:latest".format(service)
        hub_image = "{}:latest".format(repo_uri)

        # Change the tag of local docker image
        subprocess.check_call(["docker", "tag", compose_image, hub_image])

        # Push docker image to ecr
        push_operations = dict()
        push_operations[service] = subprocess.Popen([
            "docker",
            "push",
            hub_image])

        # Wait for push operations to complete.
        for service_name, popen_object in push_operations.items():
            print("Waiting for {} push to complete...".format(service_name))
            popen_object.wait()
            print("Done.")
    return


def get_cfn_output(stack_name):
    # Get output values of cloudformation template
    output_values = []
    if stack_name:
        try:
            output = cfn_client.describe_stacks(StackName=stack_name)
            for key in output['Stacks'][0]['Outputs']:
                output_values.append([key['OutputKey'], key['OutputValue']])

            for value in output_values:
                if 'ECSTaskExecRole' in value:
                    EcsTaskExecRole = value[1]
                elif 'ClusterName' in value:
                    ClusterName = value[1]
                elif 'Url' in value:
                    Url = value[1]
                elif 'ALBArn' in value:
                    AlbArn = value[1]
                elif 'PublicSubnetOne' in value:
                    PublicSubnetOne = value[1]
                elif 'PublicSubnetTwo' in value:
                    PublicSubnetTwo = value[1]
                elif 'ECSSecurityGroupId' in value:
                    ECSSecurityGroupId = value[1]
                elif 'ALBName' in value:
                    AlbName = value[1]
                elif 'ApiTargetGroupArn' in value:
                    ApiTargetGroupArn = value[1]
        except KeyError:
            print("Can't find cloudformation stack "
                  "with name {}".format(stack_name))
    return(
        EcsTaskExecRole,
        ClusterName,
        Url,
        AlbArn,
        PublicSubnetOne,
        PublicSubnetTwo,
        ECSSecurityGroupId,
        AlbName,
        ApiTargetGroupArn)


def create_task_defination(
      service,
      ecs_task_exec_role,
      repo_uri,
      volume,
      port,
      environment):
    # Create ECS Task Defination
    if service and ecs_task_exec_role \
            and repo_uri and volume and port and environment:
        try:
            ecs_client.register_task_definition(
                family='{}-taskdefination'.format(service),
                executionRoleArn=ecs_task_exec_role,
                networkMode='awsvpc',
                containerDefinitions=[
                    {
                        "portMappings": [
                            {
                                "hostPort": int(port),
                                "protocol": "tcp",
                                "containerPort": int(port)
                            }
                        ],
                        "essential": True,
                        'command': [
                            "python",
                            "./run.py"
                        ],
                        'environment': [
                            {
                                'name': 'ENV',
                                'value': environment
                            }
                        ],
                        'workingDirectory': volume,
                        'logConfiguration': {
                            'logDriver': 'awslogs',
                            'options': {
                                'awslogs-group': '/ecs/{}'.format(service),
                                'awslogs-region': 'eu-west-1',
                                'awslogs-stream-prefix': 'ecs'
                                }
                        },
                        "memoryReservation": 512,
                        "image": "{}:latest".format(repo_uri),
                        "name": "{}-service-container".format(service)
                    }
                ],
                requiresCompatibilities=['FARGATE'],
                cpu='512',
                memory='2048'
            )
            print("Task Defination Created/Updated.")
        except Exception as e:
            print("Issue while registering task defination.", e)
            return


def check_ecs_service(service, cluster_name):
    # Check if any ECS service is running or not
    try:
        response = ecs_client.describe_services(
            cluster=cluster_name,
            services=['{}-service'.format(service)]
            )
        if response['services'][0]['status'] == 'INACTIVE':
            return True
        else:
            return False
    except Exception as e:
        print("Unable to check ECS services", e)


def create_log_group(service):
    # Create Log group to store container logs
    log_group_name = '/ecs/{}'.format(service)
    response = cw_client.describe_log_groups(logGroupNamePrefix=log_group_name)
    if not response['logGroups']:
        try:
            cw_client.create_log_group(logGroupName=log_group_name)
            print("Log group create...")
        except Exception as e:
            print("Issue while creating log group.", e)
    else:
        print("Log group {} already exists.".format(log_group_name))
    return


def launch_ecs_fargate_service(
      cluster_name,
      service,
      alb_name,
      subnets,
      ecs_sg_id,
      api_target_group_arn,
      port):
    # launch fargate service
    task_definition = '{}-taskdefination'.format(service)
    try:
        ecs_client.create_service(
            cluster=cluster_name,
            serviceName='{}-service'.format(service),
            taskDefinition=task_definition,
            loadBalancers=[
                {
                    'targetGroupArn': str(api_target_group_arn),
                    'containerName': '{}-service-container'.format(service),
                    'containerPort': int(port)
                }
            ],
            desiredCount=2,
            launchType='FARGATE',
            deploymentConfiguration={
                'maximumPercent': 200,
                'minimumHealthyPercent': 100
            },
            networkConfiguration={
                'awsvpcConfiguration': {
                    'subnets': [
                        subnets[0],
                        subnets[1],
                    ],
                    'securityGroups': [
                        ecs_sg_id,
                    ],
                    'assignPublicIp': 'ENABLED'
                }
            },
            healthCheckGracePeriodSeconds=123,
            deploymentController={
                'type': 'CODE_DEPLOY'
            },
            schedulingStrategy='REPLICA'
        )
    except Exception as e:
        print("Issue while creating ecs service.", e)


def run(stackname, environment):
    # Check args
    if not stackname or not environment:
        print("Mention arguments. For eg. python deploy.py "
              "<cloudformationstackname> <environment>")
        print("Cloudformation stack is the one which"
              " you gave while uploading instructure.yaml")
        print("Environment will be development or production")
        exit(1)

    # Load the services from the input docker-compose.yml file.
    stack = yaml.load(open('docker-compose.yml'))

    # check of services in docker-compose file
    if "services" not in stack:
        print("This script expect a `services` node in docker-compose.yml")
        exit(1)

    for service in stack['services']:

        # fetch volume path and port for the service
        mapped_port = stack['services'][service]['ports']
        volume_path = stack['services'][service]['volumes']
        volume = volume_path[0].split(':', 1)[1]
        port = mapped_port[0].split(':', 1)[0]

        print("Checking service name.. ", service)
        status = check_ecr_repo(service)

        if status is not True:
            create_ecr_repo(service)

        authenticate_ecr()
        repo_uri = fetch_repo_info(service)
        build_push_image(service, repo_uri)

    # Get cloudformation output values
    output = get_cfn_output(stackname)
    ecs_task_exec_role = output[0]
    cluster_name = output[1]
    url = output[2]
    alb_arn = output[3]
    public_subnet_one = output[4]
    public_subnet_two = output[5]
    ecs_sg_id = output[6]
    alb_name = output[7]
    api_target_group_arn = output[8]

    # Create task defination
    create_task_defination(
        service,
        ecs_task_exec_role,
        repo_uri,
        volume,
        port,
        environment)

    # Check and create Cloudwatch log group
    create_log_group(service)

    # Check if ecs service exist
    ecs_service_status = check_ecs_service(service, cluster_name)
    if ecs_service_status is True or ecs_service_status is None:
        subnets = [public_subnet_one, public_subnet_two]
        # Create ECS service
        launch_ecs_fargate_service(
            cluster_name,
            service,
            alb_name,
            subnets,
            ecs_sg_id,
            api_target_group_arn,
            port)
        print("ECS service created.")
        print("Wait for 2-5 mins. Then access the API @ {} ".format(url))
    else:
        print("ECS service for {} already exists."
              "Can't create a new one unless old "
              "one is deleted.".format(service))
    return


if __name__ == '__main__':
    run(sys.argv[1], sys.argv[2])
