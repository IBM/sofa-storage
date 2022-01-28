#!/bin/bash
kubectl apply -f ./rbac-csi-sofa-storage.yaml
kubectl apply -f ./csi-driver-info.yaml
kubectl apply -f ./csi-controller.yaml
kubectl apply -f ./csi-node.yaml