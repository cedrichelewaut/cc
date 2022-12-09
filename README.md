# LOG8415_FinalProject
## AWS SET-UP
Download AWS CLI: https://aws.amazon.com/cli/ <br>
Make sure .aws/credentials file has the right security key and access token<br>
Make sure .aws/config file has following content:<br>
    [default]<br>
    region=us-east-1<br>
    output=json<br>
Install boto3, subprocess and tqdm with pip<br>
Download your personal labsuser.pem file and add it to your repository<br>
Make sure to give the labsuser.pem file the right permissions with: "yes | chmod 400 labsuser.pem"<br>

## Benchmark standalone mysql vs mysql cluster
Run standalone_vs_cluster.py
### getting benchmark results
After executing the script, 6 benchmark files will automatically be added to the repository<br>
The results from the OLTP read-only benchmarks have extention '_r'<br>
The results from the OLTP write-only benchmarks have extention '_w'<br>
The results from the OLTP read-and-write benchmarks have extention '_rw'<br>

## Cloud patterns (not finished)
! Both patterns are unable to establish connection with the cluster nodes.<br>
Aside from this, all logic is implemented
### Proxy
Have the MySQL cluster running<br>
Execute proxy_instance.py on your local device to launch the proxy <br>
Execute 'y | sudo apt-get install python3-pip' on the proxy<br>
Execute 'pip install mysql-connector' on the proxy<br>
Add proxy_server.py to the proxy<br>
Execute proxy_server.py on the proxy and answer the questions prompted<br>
Execute proxy_client.py locally and answer the questions prompted<br>
You can now query the cluster<br>

#### Gatekeeper
Have the MySQL cluster running<br>
Execute proxy_instance.py on your local device to launch the proxy <br>
Execute 'sudo apt-get install python3-pip' on the proxy<br>
Execute 'pip install mysql-connector' on the proxy<br>
Add proxy_server.py to the proxy<br>
Execute proxy_server.py on the proxy and answer the questions prompted<br>

Execute gatekeeper_instance.py on your local device to launch the gatekeeper <br>
Add gatekeeper.py to the gatekeeper<br>
Change PROXY_ADDRESS to the right ip-address for the proxy instance<br>
Execute gatekeeper.py on the gatekeeper<br>

Execute gatekeeper_client.py locally and answer the questions prompted<br>
You can now query the cluster<br>
