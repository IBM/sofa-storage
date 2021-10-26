"""
  Copyright (c) 2021 International Business Machines
  All rights reserved.
  SPDX-License-Identifier: Apache-2.0
"""
import click
import grpc
from .generated import storage_pb2
from .generated import storage_pb2_grpc

DPU_DEFAULT_URL = "192.168.100.2:50050"


@click.group()
def volume():
    pass


cli = click.CommandCollection(sources=[volume])


@volume.command()
@click.argument('subsystem_nqn', type=str)
@click.argument('pf_index', type=int, required=False)
@click.argument('vf_index', type=int, required=False)
@click.argument('serial_number', type=str, required=False)
@click.argument('model_number', type=str, required=False)
@click.option('--dpu_url', type=str)
def controller_create(subsystem_nqn, pf_index, vf_index, serial_number, model_number, dpu_url=DPU_DEFAULT_URL):
    """Create a NVMe controller on the DPU"""
    with grpc.insecure_channel(dpu_url) as channel:
        stub = storage_pb2_grpc.StorageStub(channel)
        request = storage_pb2.DPUCreateControllerRequest()
        request.subsystem_nqn = subsystem_nqn

        if pf_index is not None:
            request.pf_index = pf_index

        if vf_index is not None:
            request.vf_index = vf_index

        if serial_number is not None:
            request.serial_number = serial_number

        if model_number is not None:
            request.model_number = model_number

        rsp = stub.DPUCreateController(request)
        print(rsp)


@volume.command()
@click.argument('controller_id', type=str)
@click.option('--dpu_url', type=str)
def controller_delete(controller_id, dpu_url=DPU_DEFAULT_URL):
    """Delete a NVMe controller on the DPU"""
    with grpc.insecure_channel(dpu_url) as channel:
        stub = storage_pb2_grpc.StorageStub(channel)
        request = storage_pb2.DPUDeleteControllerRequest()
        request.controller_id = controller_id
        stub.DPUDeleteController(request)


@volume.command()
@click.argument('volume_id', type=str)
@click.argument('controller_id', type=str)
@click.argument('target_path', type=str)
@click.option('--dpu_url', type=str)
def volume_publish(volume_id, controller_id, target_path, dpu_url=DPU_DEFAULT_URL):
    """Publish a volume on the DPU host"""
    with grpc.insecure_channel(dpu_url) as channel:
        stub = storage_pb2_grpc.StorageStub(channel)
        request = storage_pb2.DPUPublishVolumeRequest()
        request.volume_id = volume_id
        request.controller_id = controller_id
        request.target_path = target_path
        stub.DPUPublishVolume(request)


@volume.command()
@click.argument('volume_id', type=str)
@click.argument('target_path', type=str)
@click.option('--dpu_url', type=str)
def volume_unpublish(volume_id, target_path, dpu_url=DPU_DEFAULT_URL):
    """Unpublish a volume on the DPU host"""
    with grpc.insecure_channel(dpu_url) as channel:
        stub = storage_pb2_grpc.StorageStub(channel)
        request = storage_pb2.DPUUnpublishVolumeRequest()
        request.volume_id = volume_id
        request.target_path = target_path
        stub.DPUUnpublishVolume(request)


if __name__ == '__main__':
    cli()
