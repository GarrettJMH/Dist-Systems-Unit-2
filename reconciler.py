from kubernetes import config, client

#connecting to the local cluster
config.load_kube_config()

#for accessing kube resources
core = client.CoreV1Api()

#for acessing custom kube resources
custom = client.CustomObjectsApi()

print("Listing pods with their IPs:")
ret = core.list_pod_for_all_namespaces(watch=False)

for _ in ret.items:
  print(i.status.pod_ip, i.metadata.namespace, i.metadata.name)

# Main loop
def main():

  

  
  while True:
    desired = get_desired_count()
    current = current_pod_count()
  
    difference = desired - current
  
    if difference > 0:
      # Create enough pods to make up the difference
  
    elif difference < 0:
      # Delete enough pods to make up the difference
  
    else:
        print("Balanced.")
