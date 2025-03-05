# TKGm Autoscaling

This repo is an example of using cluster autscaler with TKGm when also using gitops and TMC. The current OOTB approach for autoscaling in TKGm uses an overlay and the tanzu cli to install the autoscaler in the mgmt cluster and update the annotations on the workload cluster. This approach does not work well wtih TMC becuase it is client side driven. The approach outlined in the repo works by initially creating a service account in the mgmt cluster that only needs to be done once. Then on each cluster deploy the autoscaler annotations can be added to the node pools through TMC. Once TMC bootstraps the cluster with Flux the autoscaler will be installed into the workload cluster and use the service account to control scaling in the management cluster. This approach of running the autoscaler in the workload cluster is also used by VKS and is outline [here](https://cluster-api.sigs.k8s.io/tasks/automated-machine-management/autoscaling#autoscaler-running-in-workload-cluster-using-service-account-credentials-with-separate-management-cluster).  


## Pre-reqs

* jq
* kubectl
* TMC


## Setup

1. enable the CD(flux) capabilties of TMC on a cluster group and use this repo as the bootstrap repo. This example uses a common pattern of having a single cluster group bootstrap repo that dynamically determines the cluster name. You can read more about this pattern [here](https://github.com/warroyo/flux-tmc-multitenant/tree/main?tab=readme-ov-file#clustergroup-bootstrapping).