#!/bin/bash
kubectl delete -f ./csi-controller.yaml --ignore-not-found
kubectl delete -f ./csi-node.yaml --ignore-not-found
kubectl delete -f ./csi-driver-info.yaml --ignore-not-found
kubectl delete -f ./rbac-csi-sofa-storage.yaml --ignore-not-found