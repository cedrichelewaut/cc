# LOG8415_FinalProject
## AWS SET-UP
- Download AWS CLI: https://aws.amazon.com/cli/
- Make sure .aws/credentials file has security keys and access token
    - These can be downloaded from https://awsacademy.instructure.com/courses/24020/modules/items/1970541
    - Select AWS Details from menu and under "Cloud access", "AWS CLI:" click "Show"
    - Copy content to the .aws/configuration file
- Make sure .aws/config file has following content:
    [default]unnecess
    region=us-east-1
    output=json
- Install boto3, matplotlib, requests and tornado with pip
- Install boto3, matplotlib, requests, fabric and tornado with pip
- Download your personal labsuser.pem file and add it to your repository
- Make sure to give the labsuser.pem file the right permissions with: "yes | chmod 400 labsuser.pem"

## Run MySQL services
Run "MySQL_scripts/standalone.py" to create a t2.micro EC2 instance that installs MySQL stand-alone.
Run "MySQL_scripts/cluster.py" to create four t2.micro instances, including one master and three slaves.
In the cluster setup, the slaves should do read requests, master should do write requests, but we have to make sure the database is synchronized after a write
## Test the proxy pattern
Run "Proxy_scripts/proxyscript.py" in order to run the tests for the proxy pattern.
## Running whole project
In order to run the complete project, run  "project_script.py"
