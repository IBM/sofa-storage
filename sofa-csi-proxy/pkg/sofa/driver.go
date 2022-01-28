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
package sofa

import (
	"log"

	"github.com/container-storage-interface/spec/lib/go/csi"
	"github.com/ibm/sofa-storage/sofa-csi-proxy/pkg/sofa/dpu"
	"google.golang.org/grpc"
	"k8s.io/klog/v2"
)

type CSIDriver struct {
	name       string
	nodeID     string
	version    string
	cscap      []*csi.ControllerServiceCapability
	nscap      []*csi.NodeServiceCapability
	serverAddr string
	connOpts   []grpc.DialOption
	csiconn    *grpc.ClientConn
	iclient    csi.IdentityClient
	cclient    csi.ControllerClient
	nclient    csi.NodeClient
	dpuclient  dpu.StorageClient
}

func NewCSIDriver(name, v, nodeID, SofaEndpoint, CSITarget string) *CSIDriver {
	if name == "" {
		klog.Errorf("Driver name missing")
		return nil
	}

	if nodeID == "" {
		klog.Errorf("NodeID missing")
		return nil
	}
	if v == "" {
		klog.Errorf("Version argument missing")
		return nil
	}

	var opts []grpc.DialOption
	opts = append(opts, grpc.WithInsecure())
	conn, err := grpc.Dial(CSITarget, opts...)
	if err != nil {
		log.Fatalf("fail to dial: %v", err)
	}

	driver := CSIDriver{
		name:       name,
		version:    v,
		nodeID:     nodeID,
		serverAddr: CSITarget,
		connOpts:   opts,
		csiconn:    conn,
		iclient:    csi.NewIdentityClient(conn),
		cclient:    csi.NewControllerClient(conn),
		nclient:    csi.NewNodeClient(conn),
	}

	if len(SofaEndpoint) > 0 {
		var dpuopts []grpc.DialOption
		dpuopts = append(dpuopts, grpc.WithInsecure())
		dpuconn, dpuerr := grpc.Dial(SofaEndpoint, dpuopts...)
		if dpuerr != nil {
			log.Fatalf("fail to dial: %v", err)
		}
		driver.dpuclient = dpu.NewStorageClient(dpuconn)
	}

	//defer conn.Close()

	return &driver
}

func Run(conf *Config) {
	var (
		cd  *CSIDriver
		ids *IdentityServer
		cs  *ControllerServer
		ns  *NodeServer
	)
	cd = NewCSIDriver(conf.DriverName, conf.DriverVersion, conf.NodeID, conf.SofaEndpoint, conf.CSITarget)
	if cd == nil {
		klog.Fatalln("Failed to initialize CSI Driver.")
	}

	ids = NewIdentityServer(cd)

	if conf.IsNodeServer {
		ns = newNodeServer(cd)
	}

	if conf.IsControllerServer {
		cs = newControllerServer(cd)
	}

	s := NewNonBlockingGRPCServer()
	s.Start(conf.Endpoint, ids, cs, ns, conf.TestMode)
	s.Wait()
}
