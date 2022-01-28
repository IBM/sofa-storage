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
	"context"
	"time"

	"github.com/container-storage-interface/spec/lib/go/csi"
	"github.com/ibm/sofa-storage/sofa-csi-proxy/pkg/sofa/dpu"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	"k8s.io/klog/v2"
)

type IdentityServer struct {
	Driver *CSIDriver
}

func NewIdentityServer(d *CSIDriver) *IdentityServer {
	return &IdentityServer{
		Driver: d,
	}
}

func (ids *IdentityServer) GetPluginInfo(ctx context.Context, req *csi.GetPluginInfoRequest) (*csi.GetPluginInfoResponse, error) {
	if ids.Driver.name == "" {
		return nil, status.Error(codes.Unavailable, "Driver name not configured")
	}

	if ids.Driver.version == "" {
		return nil, status.Error(codes.Unavailable, "Driver is missing version")
	}

	ctxi, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	rsp, err := ids.Driver.iclient.GetPluginInfo(ctxi, req)
	if err != nil {
		return nil, err
	}
	//rsp.Name = rsp.Name + "-sofa"

	// DPU
	if ids.Driver.dpuclient != nil {
		dpureq := new(dpu.DPUGetInfoRequest)
		dpuctx, dpucancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer dpucancel()
		dpursp, dpuerr := ids.Driver.dpuclient.DPUGetInfo(dpuctx, dpureq)

		if dpuerr != nil {
			klog.Error("GetPluginInfo: %v", dpuerr.Error())
			return nil, err
		}
		klog.Info("DPU Type: %v", dpursp.DpuType)
	}

	return rsp, nil
}

// Probe check whether the plugin is running or not.
// This method does not need to return anything.
// Currently the spec does not dictate what you should return either.
// Hence, return an empty response
func (ids *IdentityServer) Probe(ctx context.Context, req *csi.ProbeRequest) (*csi.ProbeResponse, error) {
	ctxi, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	rsp, err := ids.Driver.iclient.Probe(ctxi, req)
	if err != nil {
		return nil, err
	}
	return rsp, nil
}

func (ids *IdentityServer) GetPluginCapabilities(ctx context.Context, req *csi.GetPluginCapabilitiesRequest) (*csi.GetPluginCapabilitiesResponse, error) {
	/*
		return &csi.GetPluginCapabilitiesResponse{
			Capabilities: []*csi.PluginCapability{
				{
					Type: &csi.PluginCapability_Service_{
						Service: &csi.PluginCapability_Service{
							Type: csi.PluginCapability_Service_CONTROLLER_SERVICE,
						},
					},
				},
			},
		}, nil
	*/
	ctxi, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	rsp, err := ids.Driver.iclient.GetPluginCapabilities(ctxi, req)
	if err != nil {
		return nil, err
	}
	return rsp, nil
}
