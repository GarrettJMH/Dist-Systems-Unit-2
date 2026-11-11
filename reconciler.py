# Put your code here if python is chosen for this project.

# Main loop
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
