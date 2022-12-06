import subprocess
"""-------------------get benchmark results from machine--------------------------"""  
subprocess.call(['scp', '-o','StrictHostKeyChecking=no', '-o', 'UserKnownHostsFile=/dev/null', '-i', 'labsuser.pem', "ubuntu@"+'34.239.228.54'+":/../../standalone_r.txt", '/home/cedri/cc/benchmarking_results'])
subprocess.call(['scp', '-o','StrictHostKeyChecking=no', '-o', 'UserKnownHostsFile=/dev/null', '-i', 'labsuser.pem', "ubuntu@"+'34.239.228.54'+":/../../standalone_rw.txt", '/home/cedri/cc/benchmarking_results'])
subprocess.call(['scp', '-o','StrictHostKeyChecking=no', '-o', 'UserKnownHostsFile=/dev/null', '-i', 'labsuser.pem', "ubuntu@"+'44.193.199.226'+":cluster_r.txt", '/home/cedri/cc/benchmarking_results'])
subprocess.call(['scp', '-o','StrictHostKeyChecking=no', '-o', 'UserKnownHostsFile=/dev/null', '-i', 'labsuser.pem', "ubuntu@"+'44.193.199.226'+":cluster_rw.txt", '/home/cedri/cc/benchmarking_results'])