import time
from kubernetes import config, client
from kubernetes.client.exceptions import ApiException

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

def get_resource():
  resource = custom.get_namespaced_custom_object(
    group="cosc3657.tu.ca",
    version="v1alpha1",
    namespace="default",
    plural="resilientdeployments",
    name="echo-service"  
  )

  return resource

# Grabbing count of current pods
def managed_pods():
  all_pods = core.list_namespaced_pod(
    namespace="default",
    label_selector="app.kubernetes.io/managed-by=echo-service"
  )

  return all_pods.items

def current_pod_count():
  pods = managed_pods()

  active_pods = [
    pod for pod in pods
    if pod.metadata.deletion_timestamp is None and pod.status.phase in ("Pending", "Running")
  ]

  return len(active_pods)
  

def create_pod(amount, image):
  for _ in range(amount):
    pod_def = {
            "metadata": {
                "generateName": "echo-service-",
                "labels": {
                    "app.kubernetes.io/managed-by": "echo-service"
                }
            },
            "spec": {
                "containers": [
                    {
                        "name": "echo",
                        "image": image
                    }
                ]
            }
        }
    
    pod = core.create_namespaced_pod(
      namespace="default",
      body=pod_def
    )

    print(f"Pod {pod.metadata.name} has been created.")
  

def delete_pod(amount):
  pods = [
    pod for pod in managed_pods()
    if pod.metadata.deletion_timestamp is None and pod.status.phase in ("Pending", "Running")
  ]

    for pod in pods[:amount]:
        core.delete_namespaced_pod(
            name=pod.metadata.name,
            namespace="default"
        )

      print(f"Deleted pod {pod.metadata.name}")

  
# Main running loop
def main():
  print("Controller started")
  
  while True:
    try:
      resource = get_resource()
      image = resource["spec"]["image"]
      desired = resource["spec"]["replicas"]
      current = current_pod_count()
    
      difference = desired - current
  
      print(f"\nStatus:\n"
            f"Desired pod count: {desired}\n"
            f"Current pod count: {current}\n"
            f"Difference: {difference}\n"
           )
      
      if difference > 0:
        # Create enough pods to make up the difference
        create_pod(difference, image)
    
      elif difference < 0:
        # Delete enough pods to make up the difference
        delete_pod(-difference)
  
      else:
          print("Balanced.")

    except ApiException as e:
      print(f"Kubernetes error occurred: {e}")

    except Exception as e:
      print(f"Error Occurred: {e}")

  time.sleep(2)

if __name__ == "__main__":
  main()
