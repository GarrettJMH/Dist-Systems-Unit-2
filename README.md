# Unit 2: Declarative Infrastructure & Mini-K8s Reconciliation

Welcome to **Unit 2** of COSC 3657 (Distributed Systems). In this lab, you transition from writing low-level imperative sockets to operating as a **Platform Engineer**.

Rather than issuing manual, one-off deployment commands that fail when nodes crash or network partitions occur, you will build a **declarative, self-healing control plane**. You will define custom domain abstractions using **Custom Resource Definitions (CRDs)** and write an active **Reconciliation Controller** in Python. This controller continuously observes cluster state, computes drift against user-declared specifications, and executes idempotent API operations to enforce system equilibrium under partial node failures.

---

## 📚 CDK5 Textbook Theoretical Alignment

This project operationalizes core theoretical concepts from *Distributed Systems: Concepts and Design (5th Edition)* (Coulouris, Dollimore, Kindberg, and Blair).

| Project Component | Distributed Systems Core Concept | Primary Textbook Reference |
| --- | --- | --- |
| **Cluster Topology (`kind`)** | Architectural & Physical Models, Platform vs. Middleware Abstractions | **CDK5 Sections 2.1 & 2.2** |
| **CRD Schema (`crd_definition.yaml`)** | Abstract System State Representation, Extensible Interfaces | **CDK5 Sections 1.5 & 5.2** |
| **Resource Manifest (`sample_cr.yaml`)** | Declarative Intent vs. Imperative Execution Models | **CDK5 Section 2.2** |
| **Reconciler Loop (`reconciler.py`)** | Continuous Convergence, Idempotent Remote Invocation ($f(f(x)) = f(x)$) | **CDK5 Section 5.2** |
| **Chaos Tester / Pod Eviction** | Crash-Stop Failure Model, Fail-Silent Omission, Autonomic Self-Healing | **CDK5 Section 2.4** |

---

## 🛠️ Declarative Control Loop Architecture

In an imperative workflow, operational scripts execute steps sequentially (e.g., `create_server_1()`, `create_server_2()`). If a network failure interrupts execution mid-script, the system is left in an inconsistent state.

In contrast, our custom controller implements a **Continuous Reconciliation Control Loop**:

```text
       +---------------------------------------------------+
       |                                                   |
       v                                                   |
[ Observe Live State ] ---> [ Compute State Drift ] ---> [ Reconcile ]
  (Query Pod API)             (Delta = Desired - Actual)    (Create/Delete Pods)

```

1. **Desired State ($N_{\text{desired}}$):** Parsed from the user's `ResilientDeployment` manifest stored in `etcd`.


2. **Observed State ($N_{\text{observed}}$):** Discovered by querying active, running pods matching the resource label.


3. **State Drift ($\Delta$):** Calculated continuously as:

$$\Delta = N_{\text{desired}} - N_{\text{observed}}$$

* If $\Delta > 0$: The controller provisions $\Delta$ replacement pods.
* If $\Delta < 0$: The controller prunes $\vert{}\Delta\vert{}$ excess pods.
* If $\Delta = 0$: The cluster is in **Equilibrium**.

---

## 📁 Repository Structure

```text
fw26-unit2-student/
├── crd_definition.yaml         # Kubernetes Custom Resource Definition schema
├── sample_cr.yaml              # Custom Resource declarative intent manifest
├── reconciler.py               # Active Reconciliation Controller (or reconciler in your preferred language) implementation
└── README.md                   # Project documentation & instructions

```

---

## 🚀 Quick Start Instructions

### Install Docker, Kind and kubectl to your OS as per the section [Host Prerequisites & Quick Tooling Installation Guide](#host-prerequisites-and-quick-tooling-installation-guide)

### Install python libraries if python is chosen for this project.

```bash
python3 -m venv venv && source venv/bin/activate
pip install kubernetes rich pyyaml

```

---

## 🧪 Step-by-Step Testing & Verification Instructions

### Step 1: Provision Local Kubernetes Cluster

Inside the integrated terminal, spin up a multi-node `kind` cluster:

```bash
kind create cluster --name cosc3657-unit2

```

Verify that `kubectl` is connected to your local cluster:

```bash
kubectl get nodes

```

### Step 2: Register the Custom Resource Definition (CRD)

Apply `crd_definition.yaml` to register the `ResilientDeployment` schema with the API server:

```bash
kubectl apply -f crd_definition.yaml

```

Verify registration:

```bash
kubectl get crd resilientdeployments.cosc3657.tu.ca

```

### Step 3: Launch the Reconciliation Controller

In Terminal 1, run the controller:

```bash
python reconciler.py

```

*Expected Output:*

```text
=== COSC 3657 Custom Kubernetes Reconciler Started ===

```

### Step 4: Apply Declarative Intent Manifest

Open a split terminal (`Ctrl+Shift+\``) and apply `sample_cr.yaml`:

```bash
kubectl apply -f sample_cr.yaml

```

Observe Terminal 1. The reconciler detects $\Delta = +3$ and provisions 3 pods automatically:

```text
[RECONCILE LOOP] Resource: echo-cluster | Desired: 3 | Observed: 0 | Drift: 3
Scale-Up Event: Provisioning 3 pod(s) to resolve drift...
EQUILIBRIUM REACHED: System state matches target spec for 'echo-cluster'.

```

Verify pod creation in Terminal 2:

```bash
kubectl get pods -l app.kubernetes.io/managed-by=echo-cluster

```

### Step 5: Fault Injection & Self-Healing Verification

Simulate an unannounced process crash under the **Crash-Stop Failure Model** by forcibly deleting a running pod:

```bash
kubectl delete pod $(kubectl get pods -l app.kubernetes.io/managed-by=echo-cluster -o jsonpath='{.items[0].metadata.name}') --grace-period=0 --force

```

Watch Terminal 1. Within 2 seconds, the controller registers $\Delta = +1$ and recreates a replacement pod automatically to restore target equilibrium.

### Step 6: Test Declarative Scale Mutation

Mutate the desired replica count from `3` to `5` without restarting the controller:

```bash
kubectl patch resilientdeployment echo-cluster --type='json' -p='[{"op": "replace", "path": "/spec/replicas", "value": 5}]'

```

*Expected Output in Terminal 1:* The controller detects $\Delta = +2$ and scales up 2 additional pods.

---

## 📝 Student Deliverables Checklist

* [ ] Create your own Mini-K8s cluster and apply the provided custom resource definition `crd_definition.yaml`.
* [ ] Complete implementation of `reconciler.py` (or in any other your preferred language) so it can handle watch events, calculating drift, and performing idempotent scale operations.
* [ ] Terminal screenshot/log recording demonstrating that forcibly deleting a pod via `kubectl delete pod --force` causes the reconciler to automatically provision a replacement pod.
* [ ] Record the presentation of your code, also explain what challenges encountered and overcomed, as well as how AI used to help this project if AI is used.
* [ ] Submit your github repository with the completed code.

---

## 📖 Related Reference Documents

If you are new to Kubernetes or cloud-native control planes, review these curated resources alongside the CDK5 textbook readings to build a strong foundation.

### 1. Fundamental Kubernetes Architecture & Concepts

* **[Kubernetes Components Overview](https://kubernetes.io/docs/concepts/overview/components/):** Understand the division between the **Control Plane** (`kube-apiserver`, `etcd`) and **Worker Nodes** (`kubelet`, `container runtime`).


* **[Kubernetes Pod Lifecycle](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/):** Learn how pods transition through states (`Pending`, `Running`, `Failed`, `Terminating`), which our reconciler evaluates during state drift calculation.


* **[Declarative Management vs. Imperative Commands](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/declarative-config/):** Understand why managing state through configuration files (`YAML`) provides resilience compared to one-off imperative shell scripts.



### 2. Custom Resources & The Controller Pattern

* **[Custom Resources & CRDs Explained](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/):** Learn how Custom Resource Definitions extend the base Kubernetes API schema with custom domain models.


* **[The Kubernetes Controller Pattern](https://kubernetes.io/docs/concepts/architecture/controller/):** Read the official guide on reconciliation loops and how background controllers continuously work to drive actual cluster state toward declared target state.


* **[Operator Pattern Design Principles](https://kubernetes.io/docs/concepts/extend-kubernetes/operator/):** Learn how real-world platform operators automate state management and fault recovery.



### 3. Client Libraries & Local Tooling

* **[Python Client for Kubernetes (`kubernetes-client`)](https://github.com/kubernetes-client/python):** Reference documentation for interacting with `CustomObjectsApi` and `CoreV1Api` in Python[cite: 8].
* **[Python Watch API Example](https://www.google.com/search?q=https://github.com/kubernetes-client/python/blob/master/examples/watch/pod_watch.py):** See how to stream live API server events asynchronously instead of polling[cite: 8].
* **[Kind (Kubernetes in Docker) Quick Start](https://kind.sigs.k8s.io/docs/user/quick-start/):** Guide on how `kind` provisions multi-node Kubernetes clusters inside local Docker containers[cite: 5, 8].
* **[kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/):** Quick reference for `kubectl get`, `kubectl apply`, `kubectl delete`, and JSONPath field filtering[cite: 8].


## Host Prerequisites and Quick Tooling Installation Guide

Use the quick-start commands below to install Docker, `kubectl`, and `kind` across **macOS**, **Windows**, or **Ubuntu Linux** for setting up your local environment outside or alongside Dev Containers.

---

### 🍎 macOS Quick Start

Install all dependencies using [Homebrew](https://brew.sh/):

```bash
# 1. Install Docker Desktop
brew install --cask docker

# 2. Install Kubernetes CLI and Kind
brew install kubectl kind

```

> **Note:** Launch **Docker.app** from your `Applications` folder after installation to initialize the container daemon.

---

### 🪟 Windows Quick Start

Execute the following commands in **PowerShell (Run as Administrator)**:

1. **Enable WSL 2 (Required for Docker Engine):**
```powershell
wsl --install

```


*(Restart your machine if prompted before proceeding).*
2. **Install Docker Desktop, `kubectl`, and `kind`:**
* **Option A: Using `winget` (Built-in Package Manager)**
```powershell
winget install Docker.DockerDesktop
winget install Kubernetes.kubectl
winget install Kubernetes.kind

```


* **Option B: Using `chocolatey**`
```powershell
choco install docker-desktop kubernetes-cli kind

```





> **Note:** Open **Docker Desktop**, navigate to **Settings $\rightarrow$ General**, and ensure **"Use the WSL 2 based engine"** is enabled.

---

### 🐧 Ubuntu Linux Quick Start

Execute the following commands in your terminal (Ubuntu 20.04 / 22.04 / 24.04 LTS):

1. **Install Docker Engine & Configure Non-Root Permissions:**
```bash
sudo apt-get update && sudo apt-get install -y ca-certificates curl gnupg docker.io
sudo usermod -aG docker $USER
newgrp docker

```


2. **Install `kubectl` Binary:**
```bash
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
rm kubectl

```


3. **Install Architecture-Aware `kind` Binary:**
```bash
ARCH=$(uname -m)
if [ "$ARCH" = "x86_64" ]; then KIND_ARCH="amd64"; else KIND_ARCH="arm64"; fi
curl -Lo ./kind "https://kind.sigs.k8s.io/dl/v0.22.0/kind-linux-${KIND_ARCH}"
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind

```



---

### 🧪 Tooling Verification Check

Execute these commands in your host terminal to verify that all components are operational before creating your cluster:

1. **Verify Container Runtime:**
```bash
docker run --rm hello-world

```


2. **Verify CLI Tool Versions:**
```bash
kubectl version --client
kind --version

```


3. **Test Cluster Provisioning:**
```bash
kind create cluster --name quickstart-test
kubectl get nodes
kind delete cluster --name quickstart-test

```