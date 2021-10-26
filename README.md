# sofa-storage
Storage Management for Secure Offload FrAmework (SOFA) for the Cloud


## Running

### DPU

To run the GRPC server on the DPU you can simply run

```
make run
```

### Control plane example

To run the example control plane server run:

```
make example-run
```

After the control plane is up you can use the CLI client to initiate various operations:

```
python -m example.ctrl_cli list
python -m example.ctrl_cli create sofa_volume_3 10737418240
python -m example.ctrl_cli create-controller nqn flex24 (pf index) (vf index) (serial number) (model number)
python -m example.ctrl_cli attach sofa_volume_3 vm_id controller_id flex24 network '/dev/nvme0n2' (key)
python -m example.ctrl_cli detach sofa_volume_3 flex24 '/dev/nvme0n2'
python -m example.ctrl_cli delete-controller 020 flex24
python -m example.ctrl_cli delete sofa_volume_3
```

## Running a VM

### Preparing the volume

The following example creates a volume, converts a qcow2 image to raw and then copies
the contents to the volume/partition.

```
python -m example.ctrl_cli create sofa_volume_3 10737418240
qemu-img convert /home/pol/CentOS-8-ec2-8.3.2011-20201204.2.x86_64.qcow2 -O raw CentOS-8-ec2-8.3.2011-20201204.2.x86_64.raw
sudo dd if=/home/pol/CentOS-8-ec2-8.3.2011-20201204.2.x86_64.raw of=/dev/ceph-5fa337db-fdad-4faf-96f5-9ad622e4ab39/sofa_volume_3
```

### Running the VM

The following will attach the volume and then create the VM.

```
python -m example.ctrl_cli attach sofa_volume_3 zac12 '/dev/nvme0n2'
sudo virt-install --name CentOS_8_Server --memory 2048 --vcpus 1 --disk /dev/nvme0n2,bus=virtio --import --os-variant centos8 --network default
```

PCI passthrough to the VM:
```
sudo virt-install --name Ubuntu1PCI --memory 2048 --vcpus 1 --hostdev PCI-BDF --import --network default --location 'http://gb.archive.ubuntu.com/ubuntu/dists/bionic/main/installer-amd64/' —disk none —boot uefi
```


## Authors

- Nikolas Ioannou <nio@zurich.ibm.com>
- Jonas Pfefferle <jpf@zurich.ibm.com>
- Raphael Polig <pol@zurich.ibm.com>
- Daniel Trujillo
