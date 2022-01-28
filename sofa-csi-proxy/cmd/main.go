//
// Copyright 2022 IBM Corporation
// SPDX-License-Identifier: Apache-2.0
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//
package main

import (
	"flag"
	"os"

	"github.com/ibm/sofa-storage/sofa-csi-proxy/pkg/sofa"
	"k8s.io/klog/v2"
)

const (
	driverName    = "sofa.ibm.com"
	driverVersion = "0.1.0"
)

var (
	conf = sofa.Config{
		DriverVersion: driverVersion,
	}
)

func init() {
	flag.StringVar(&conf.DriverName, "drivername", driverName, "Name of the driver")
	flag.StringVar(&conf.Endpoint, "endpoint", "unix://csi/sofacsi.sock", "CSI endpoint")
	flag.StringVar(&conf.NodeID, "nodeid", "", "node id")
	flag.BoolVar(&conf.IsControllerServer, "controller", true, "Start controller server")
	flag.BoolVar(&conf.IsNodeServer, "node", true, "Start node server")
	flag.StringVar(&conf.SofaEndpoint, "sofa", "", "SOFA endpoint")
	flag.StringVar(&conf.CSITarget, "csitarget", "", "Target CSI endpoint")

	klog.InitFlags(nil)
	if err := flag.Set("logtostderr", "true"); err != nil {
		klog.Exitf("failed to set logtostderr flag: %v", err)
	}
	flag.Parse()
}

func main() {
	klog.Infof("Starting SOFA-CSI driver: %v version: %v", driverName, driverVersion)

	namespaces := sofa.GetNVMeNamespaces()
	for _, namespace := range namespaces {
		klog.Infof("nsid: %v, uuid: %v, devpath: %v", namespace.Nsid, namespace.Uuid, namespace.DevPath)
	}
	klog.Infof("NodeID: %v", conf.NodeID)

	if len(conf.SofaEndpoint) == 0 {
		klog.Info("Not using SOFA")
	} else {
		klog.Infof("Using SOFA @ %v", conf.SofaEndpoint)
	}

	if len(conf.CSITarget) == 0 {
		klog.Fatal("csitarget must be set")
		os.Exit(1)
	} else {
		klog.Infof("Using CSI Target @ %v", conf.CSITarget)
	}

	sofa.Run(&conf)

	os.Exit(0)
}
