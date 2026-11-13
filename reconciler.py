from kubernetes import config, client

# Connecting to the local cluster
config.load_kube_config()

# For accessing kube resources
core = client.CoreV1Api()

# For acessing custom kube resources
custom = client.CustomObjectsApi()

# Listing pods and ips (FOR TESTING)
print("Listing pods with their IPs:")
ret = core.list_pod_for_all_namespaces(watch=False)

for i in ret.items:
  print(i.status.pod_ip, i.metadata.namespace, i.metadata.name)


# Grabbing required resource replica count
def get_desired_count():
  resource = custom.get_namespaced_custom_object(
    group="cosc3657.tu.ca",
    version="v1alpha1",
    namespace="default",
    plural="resilientdeployments",
    name="echo-service"  
  )

  return resource["spec"]["replicas"]

# Grabbing count of current pods
def current_pod_count():
  pods = core.list_namespaced_pod(
    namespace="default",
    label_selector="app.kubernetes.io/managed-by=echo-cluster"
  )

  return len(pods.items)

def create_pod(amount):
  for _ in range(amount):
    core.create_namespaced_pod()
  

def delete_pod(amount):
  for _ in range(amount):
    core.delete_namespaced_pod()


# Test to ensure get_desired_count() works
print("Desired pods:", get_desired_count())
  
# Main running loop
def main():
  while True:
    desired = get_desired_count()
    current = current_pod_count()
  
    difference = desired - current
  
    if difference > 0:
      # Create enough pods to make up the difference
      create_pod(difference)
  
    elif difference < 0:
      # Delete enough pods to make up the difference
      delete_pod(-difference)

    else:
        print("Balanced.")
