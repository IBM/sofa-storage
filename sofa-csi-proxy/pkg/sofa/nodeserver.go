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
	"errors"
	"os"
	"regexp"
	"time"

	"github.com/container-storage-interface/spec/lib/go/csi"
	"github.com/ibm/sofa-storage/sofa-csi-proxy/pkg/sofa/dpu"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	"k8s.io/klog/v2"
	mount "k8s.io/mount-utils"
)

type NodeServer struct {
	Driver  *CSIDriver
	mounter mount.Interface
}

func newNodeServer(d *CSIDriver) *NodeServer {
	return &NodeServer{
		Driver:  d,
		mounter: mount.New(""),
	}
}

func (ns *NodeServer) NodePublishVolume(ctx context.Context, req *csi.NodePublishVolumeRequest) (*csi.NodePublishVolumeResponse, error) {
	volumeID := req.GetVolumeId()
	if volumeID == "" {
		return nil, status.Error(codes.InvalidArgument, "Volume ID missing in request")
	}
	targetPath := req.GetTargetPath()
	if targetPath == "" {
		return nil, status.Error(codes.InvalidArgument, "Target path not provided")
	}
	volCap := req.GetVolumeCapability()
	if volCap == nil {
		return nil, status.Error(codes.InvalidArgument, "Volume capability missing in request")
	}
	//mountOptions := volCap.GetMount().GetMountFlags()
	var mountOptions []string
	if req.GetReadonly() {
		mountOptions = append(mountOptions, "ro")
	}
	klog.Info("NodePublishVolume: Received all request arguments")

	// CSI
	ctxi, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	_, err := ns.Driver.nclient.NodePublishVolume(ctxi, req)
	if err != nil {
		return nil, err
	}

	// DPU
	var volume_uuid string
	if ns.Driver.dpuclient != nil {
		klog.InfoS("Requesting DPU to publish volume: %v", req.VolumeId)
		re := regexp.MustCompile(`\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}`)
		match := re.FindStringSubmatch(req.VolumeId)
		if len(match) == 0 {
			return nil, status.Error(codes.Internal, "no UUID found in volume id")
		}
		volume_uuid = match[0]
		dpuctx, dpucancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer dpucancel()
		_, dpuerr := ns.Driver.dpuclient.DPUPublishVolume(dpuctx, &dpu.DPUPublishVolumeRequest{
			VolumeId:     volume_uuid,
			ControllerId: "NvmeEmu0pf0",
			TargetPath:   req.TargetPath})
		if dpuerr != nil {
			return nil, dpuerr
		}
		klog.Info("DPU published volume: %v", req.VolumeId)
	}
	//return rsp, nil

	var source string
	for len(source) == 0 {
		time.Sleep(time.Duration(100) * time.Millisecond)
		namespaces := GetNVMeNamespaces()
		for _, namespace := range namespaces {
			klog.Infof("nsid: %v, uuid: %v, devpath: %v", namespace.Nsid, namespace.Uuid, namespace.DevPath)
			if namespace.Uuid == volume_uuid {
				source = namespace.DevPath
				break
			}
		}
	}
	if len(source) == 0 {
		return nil, status.Error(codes.Internal, "failed to get devpath")
	}

	klog.Info("NodePublishVolume: Setting mountPermissions")
	mountPermissions := 0777
	klog.Info("NodePublishVolume: Calling mounter.IsLikelyNotMountPoint")
	notMnt, err := ns.mounter.IsLikelyNotMountPoint(targetPath)
	if err != nil {
		if os.IsNotExist(err) {
			klog.Info("NodePublishVolume: Creating mount point")
			if err := os.MkdirAll(targetPath, os.FileMode(mountPermissions)); err != nil {
				return nil, status.Error(codes.Internal, err.Error())
			}
			notMnt = true
		} else {
			return nil, status.Error(codes.Internal, err.Error())
		}
	}
	if !notMnt {
		return &csi.NodePublishVolumeResponse{}, nil
	}
	/*
		var dev_ready = false
		var dev_ready_tests = 0
		for !dev_ready {
			if _, err := os.Stat(source); err == nil {
				// path/to/whatever exists
				dev_ready = true
				break
			}
			dev_ready_tests++
			if dev_ready_tests > 50 {
				klog.Warning("Device not ready after 5s")
				break
			}
			time.Sleep(time.Duration(100) * time.Millisecond)
		} */

	var mount_tries = 0
	for {
		klog.Infof("NodePublishVolume: Mounting volumeID(%v) source(%s) targetPath(%s) mountflags(%v)", volumeID, source, targetPath, mountOptions)
		err = ns.mounter.Mount(source, targetPath, "", mountOptions)
		mount_tries++
		// SUCCESS
		if err == nil {
			return &csi.NodePublishVolumeResponse{}, nil
		}

		if mount_tries > 50 {
			break
		}
		time.Sleep(time.Duration(100) * time.Millisecond)
	}
	return nil, status.Error(codes.Internal, err.Error())

}

func (ns *NodeServer) NodeUnpublishVolume(ctx context.Context, req *csi.NodeUnpublishVolumeRequest) (*csi.NodeUnpublishVolumeResponse, error) {
	volumeID := req.GetVolumeId()
	if volumeID == "" {
		return nil, status.Error(codes.InvalidArgument, "Volume ID missing in request")
	}
	targetPath := req.GetTargetPath()
	if targetPath == "" {
		return nil, status.Error(codes.InvalidArgument, "Target path missing in request")
	}

	// HOST UMOUNT
	notMnt, err := ns.mounter.IsLikelyNotMountPoint(targetPath)

	if err != nil {
		if os.IsNotExist(err) {
			return nil, status.Error(codes.NotFound, "Targetpath not found")
		}
		return nil, status.Error(codes.Internal, err.Error())
	}
	if notMnt {
		return nil, status.Error(codes.NotFound, "Volume not mounted")
	}

	klog.V(2).Infof("NodeUnpublishVolume: CleanupMountPoint %s on volumeID(%s)", targetPath, volumeID)
	err = mount.CleanupMountPoint(targetPath, ns.mounter, false)
	if err != nil {
		return nil, status.Error(codes.Internal, err.Error())
	}

	// DPU
	if ns.Driver.dpuclient != nil {
		klog.InfoS("Requesting DPU to unpublish volume: %v", req.VolumeId)
		re := regexp.MustCompile(`\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}`)
		match := re.FindStringSubmatch(req.VolumeId)
		if len(match) == 0 {
			return nil, errors.New("no UUID found in volume id")
		}
		volume_uuid := match[0]
		var volume_nsid string
		namespaces := GetNVMeNamespaces()
		for _, namespace := range namespaces {
			klog.Infof("nsid: %v, uuid: %v", namespace.Nsid, namespace.Uuid)
			if volume_uuid == namespace.Uuid {
				volume_nsid = namespace.Nsid
				break
			}
		}
		klog.InfoS("Requesting DPU to unpublish nsid: %v", volume_nsid)
		dpuctx, dpucancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer dpucancel()
		_, dpuerr := ns.Driver.dpuclient.DPUUnpublishVolume(dpuctx, &dpu.DPUUnpublishVolumeRequest{VolumeId: volume_nsid, TargetPath: req.TargetPath})
		if dpuerr != nil {
			return nil, dpuerr
		}
		klog.Info("DPU unpublished volume: %v", req.VolumeId)
	}

	// CSI
	ctxi, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	_, err = ns.Driver.nclient.NodeUnpublishVolume(ctxi, req)
	if err != nil {
		return nil, err
	}
	//return rsp, nil
	return &csi.NodeUnpublishVolumeResponse{}, nil

}

// NodeGetInfo return info of the node on which this plugin is running
func (ns *NodeServer) NodeGetInfo(ctx context.Context, req *csi.NodeGetInfoRequest) (*csi.NodeGetInfoResponse, error) {
	return &csi.NodeGetInfoResponse{
		NodeId: ns.Driver.nodeID,
	}, nil
}

// NodeGetCapabilities return the capabilities of the Node plugin
func (ns *NodeServer) NodeGetCapabilities(ctx context.Context, req *csi.NodeGetCapabilitiesRequest) (*csi.NodeGetCapabilitiesResponse, error) {
	return &csi.NodeGetCapabilitiesResponse{
		Capabilities: ns.Driver.nscap,
	}, nil
}

// NodeGetVolumeStats get volume stats
func (ns *NodeServer) NodeGetVolumeStats(ctx context.Context, req *csi.NodeGetVolumeStatsRequest) (*csi.NodeGetVolumeStatsResponse, error) {
	if req.VolumeId == "" {
		return nil, status.Error(codes.InvalidArgument, "NodeGetVolumeStats volume ID was empty")
	}
	if req.VolumePath == "" {
		return nil, status.Error(codes.InvalidArgument, "NodeGetVolumeStats volume path was empty")
	}

	return &csi.NodeGetVolumeStatsResponse{}, nil
}

// NodeUnstageVolume unstage volume
func (ns *NodeServer) NodeUnstageVolume(ctx context.Context, req *csi.NodeUnstageVolumeRequest) (*csi.NodeUnstageVolumeResponse, error) {
	return nil, status.Error(codes.Unimplemented, "")
}

// NodeStageVolume stage volume
func (ns *NodeServer) NodeStageVolume(ctx context.Context, req *csi.NodeStageVolumeRequest) (*csi.NodeStageVolumeResponse, error) {
	return nil, status.Error(codes.Unimplemented, "")
}

// NodeExpandVolume node expand volume
func (ns *NodeServer) NodeExpandVolume(ctx context.Context, req *csi.NodeExpandVolumeRequest) (*csi.NodeExpandVolumeResponse, error) {
	return nil, status.Error(codes.Unimplemented, "")
}
