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
	"fmt"
	"io/ioutil"
	"path/filepath"
	"regexp"
	"strings"

	"github.com/kubernetes-csi/csi-lib-utils/protosanitizer"
	"google.golang.org/grpc"
	"k8s.io/klog/v2"
)

type Config struct {
	DriverName    string
	DriverVersion string
	Endpoint      string
	NodeID        string

	IsControllerServer bool
	IsNodeServer       bool

	TestMode bool

	SofaEndpoint string
	CSITarget    string
}

func parseEndpoint(ep string) (proto, addr string, _ error) {
	if strings.HasPrefix(strings.ToLower(ep), "unix://") || strings.HasPrefix(strings.ToLower(ep), "tcp://") {
		s := strings.SplitN(ep, "://", 2)
		if s[1] != "" {
			return s[0], s[1], nil
		}
	}
	return "", "", fmt.Errorf("invalid endpoint: %v", ep)
}

func logGRPC(ctx context.Context, req interface{}, info *grpc.UnaryServerInfo, handler grpc.UnaryHandler) (interface{}, error) {
	klog.V(3).Infof("GRPC call: %s", info.FullMethod)
	klog.V(5).Infof("GRPC request: %s", protosanitizer.StripSecrets(req))
	resp, err := handler(ctx, req)
	if err != nil {
		klog.Errorf("GRPC error: %v", err)
	} else {
		klog.V(5).Infof("GRPC response: %s", protosanitizer.StripSecrets(resp))
	}
	return resp, err
}

type NVMeNamespace struct {
	Uuid    string
	Nsid    string
	DevPath string
}

func GetNVMeNamespaces() []NVMeNamespace {
	klog.V(5).Infof("GetNVMeNamespaces")
	var namespaces []NVMeNamespace
	path := "/sys/class/nvme"
	dirs, err := ioutil.ReadDir(path)
	if err == nil {
		for _, nvme_dir := range dirs {
			the_dir := filepath.Join(path, nvme_dir.Name())
			klog.V(5).Infof("nvme_dir: %s", the_dir)
			// READ model file and check "Mellanox NVMe SNAP Controller"
			buf, _ := ioutil.ReadFile(filepath.Join(the_dir, "/model"))
			controller_model := strings.TrimSpace(string(buf))
			klog.V(5).Infof("controller_model: %s", controller_model)
			if controller_model == "Mellanox NVMe SNAP Controller" {
				klog.V(5).Infof("Get the namespaces")
				matches, _ := filepath.Glob(filepath.Join(the_dir, "nvme*"))
				//var dirs []string
				for _, match := range matches {
					//f, _ := os.Stat(match)
					klog.V(5).Infof("match: %s", match)
					nsid_buf, _ := ioutil.ReadFile(filepath.Join(match, "/nsid"))
					nsid_str := strings.TrimSpace(string(nsid_buf))
					//nsid, _ := strconv.Atoi(nsid_str)

					uuid_buf, _ := ioutil.ReadFile(filepath.Join(match, "/uuid"))
					uuid_str := strings.TrimSpace(string(uuid_buf))

					re := regexp.MustCompile(`[0-9]+$`)
					dev_nsid_matches := re.FindStringSubmatch(match)
					dev_nsid := dev_nsid_matches[0]
					dev_path := filepath.Join("/dev", nvme_dir.Name()+"n"+dev_nsid)
					namespaces = append(namespaces, NVMeNamespace{Uuid: uuid_str, Nsid: nsid_str, DevPath: dev_path})
					//if f.IsDir() {
					//dirs = append(dirs, match)
					//}
				}
			}

		}
	} else {
		klog.Error(err)
	}
	return namespaces
}
