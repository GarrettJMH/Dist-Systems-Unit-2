import time
import threading
from kubernetes import config, client, watch
from kubernetes.client.exceptions import ApiException

# Connecting to the local cluster
config.load_kube_config()

# For accessing kube resources
core = client.CoreV1Api()

# For acessing custom kube resources
custom = client.CustomObjectsApi()

event_marker = threading.Event()

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

def clean_terminals():
  for pod in managed_pods():
    if pod.status.phase in ("Succeeded", "Failed"):
      core.delete_namespaced_pod(
        name=pod.metadata.name,
        namespace="default"
      )
      print(f"Deleted pod {pod.metadata.name} due to terminal state: {pod.status.phase}")

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

def watch_pods():
  resource_version = None

  while True:
    try:
      if resource_version is None:
        pod_list = core.list_namespaced_pod(
          namespace="default",
          label_selector="app.kubernetes.io/managed-by=echo-service"
        )
        resource_version = pod_list.metadata.resource_version
        event_marker.set() # Initial event signal

      w = watch.Watch()

      for event in w.stream(
        core.list_namespaced_pod,
        namespace="default",
        label_selector="app.kubernetes.io/managed-by=echo-service",
        timeout_seconds=15,
        resource_version=resource_version
      ):
        resource_version = event['raw_object']['metadata']['resourceVersion']
        print(f"Pod event: {event['type']}")
        event_marker.set() # Event signal (for pods)

    except ApiException as e:

      if e.status == 410:
        resource_version = None # AI-suggested reset of resource version if version is too old

      else:
        print(f"Kubernetes API error in watch_pods: {e}")
        time.sleep(2) # Wait for retry
    
    except Exception as e:
      print(f"Error in watch_pods: {e}")
      time.sleep(2) # Wait for retry

def watch_resource():

  resource_version = None

  while True:

    try:

      if resource_version is None:
        resource_list = custom.list_namespaced_custom_object(
          group="cosc3657.tu.ca",
          version="v1alpha1",
          namespace="default",
          plural="resilientdeployments"
        )

        resource_version = resource_list["metadata"]["resourceVersion"]
        event_marker.set() # Initial event signal

      w = watch.Watch()

      for event in w.stream(
        custom.list_namespaced_custom_object,
        group="cosc3657.tu.ca",
        version="v1alpha1",
        namespace="default",
        plural="resilientdeployments",
        timeout_seconds=15,
        resource_version=resource_version
      ):
        resource_version = event['raw_object']['metadata']['resourceVersion']
        print(f"Resource event: {event['type']}")
        event_marker.set() # Event signal (for resources)

    except ApiException as e:

      if e.status == 410:
        resource_version = None # AI-suggested reset of resource version if version is too old

      else:
        print(f"Kubernetes API error in watch_resource: {e}")
        time.sleep(2) # Wait for retry

    except Exception as e:
      print(f"Error in watch_resource: {e}")
      time.sleep(2) # Wait for retry

# Main running loop
def main():
  print("Controller started")

  threading.Thread(target=watch_pods, daemon=True).start()
  threading.Thread(target=watch_resource, daemon=True).start()
  
  while True:

    event_marker.clear() # Clear event before waiting for new ones

    try:
      resource = get_resource()
      image = resource["spec"]["image"]
      desired = resource["spec"]["replicas"]
      clean_terminals()
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

    event_marker.wait(timeout=2) # Wait for event before a recheck

if __name__ == "__main__":
  main()
