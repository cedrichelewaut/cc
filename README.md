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
- Install boto3, matplotlib, requests, fabric and tqdm with pip
- Download your personal labsuser.pem file and add it to your repository
- Make sure to give the labsuser.pem file the right permissions with: "yes | chmod 400 labsuser.pem"

## Benchmark standalone mysql mode and mysql cluster
Run standalone_vs_cluster.py
### Automation not working yet
ssh into master and execute all commands in 'master_commands' found in standalone_vs_cluster.py <br>
ssh into each slave and execute all commands in 'slave_commands' found in standalone_vs_cluster.py <br>
ssh into master and execute all commands in 'start_mysqlc_mgmd' found in standalone_vs_cluster.py <br>
ssh into master and execute all commands in 'sakila_commands' found in standalone_vs_cluster.py <br>
### getting benchmark results
Use scp to retrieve the results file from the nodes
"scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i labsuser.pem ubuntu@<ip-address-standalone>:/../../standalone.txt" <br>
"scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i labsuser.pem ubuntu@<ip-address-cluster-master>:cluster.txt" <br>

## the proxy
execute proxy_instance.py on your local device  <br>
wait untill the ec2 instance is launched <br>
change the host in proxy_client.py to the public-ip address of the launches ec2 instance
add proxy_server.py to the ec2 instance <br>
run proxy_server.py on the ec2 instance via "python3 proxy_server.py <mode>". <br>
For mode you can choose between: 'direct', 'custom' and 'random'<br>
execute proxy_client.py on your local device  <br>

