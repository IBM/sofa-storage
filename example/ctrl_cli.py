"""
  Copyright (c) 2021 International Business Machines
  All rights reserved.
  SPDX-License-Identifier: Apache-2.0
"""
import grpc
import click

from .generated import storage_ctrl_pb2_grpc, storage_ctrl_pb2

CTRL_DEFAULT_URL = "localhost:50051"


@click.group()
def volume():
    pass


@volume.command()
@click.argument('name', type=str)
@click.argument('capacity_bytes', type=int)
@click.option('--source_image', type=str)
@click.option('--ctrl_url', type=str)
def create(name, capacity_bytes, source_image=None, ctrl_url=CTRL_DEFAULT_URL):
    """Create volume"""
    with grpc.insecure_channel(ctrl_url) as channel:
        stub = storage_ctrl_pb2_grpc.CtrlStub(channel)
        request = storage_ctrl_pb2.CTRLCreateVolumeRequest()
        request.name = name
        request.capacity_bytes = capacity_bytes
        if source_image is not None:
            request.volume_content_source.volume.volume_id = source_image  # pylint: disable=E1101
        stub.CTRLCreateVolume(request)


@volume.command()
@click.argument('volume_id', type=str)
@click.argument('controller_id', type=str)
@click.argument('node_id', type=str)
@click.argument('network', type=str)
@click.argument('target_path', type=str)
@click.argument('encryption_key', type=str, required=False)
@click.option('--ctrl_url', type=str)
def attach(volume_id, controller_id, node_id, network, target_path, encryption_key, ctrl_url=CTRL_DEFAULT_URL):
    """Attach volume"""
    with grpc.insecure_channel(ctrl_url) as channel:
        stub = storage_ctrl_pb2_grpc.CtrlStub(channel)
        request = storage_ctrl_pb2.CTRLAttachVolumeRequest()
        request.volume_id = volume_id
        request.controller_id = controller_id
        request.node_id = node_id
        request.network = network
        request.target_path = target_path

        if encryption_key and len(encryption_key) == 16:  # 16 x 8 = 128 bits, which is length of AES-CBC
            request.secrets['encryption_key'] = encryption_key  # pylint: disable=E1101
        elif encryption_key:
            print('Encryption key must be length 128 bits (16 integers)')
            return

        stub.CTRLAttachVolume(request)
    print('Attach volume response:')


@volume.command()
@click.argument('volume_id', type=str)
@click.argument('node_id', type=str)
@click.argument('target_path', type=str)
@click.option('--ctrl_url', type=str)
def detach(volume_id, node_id, target_path, ctrl_url=CTRL_DEFAULT_URL):
    """Detach volume"""
    with grpc.insecure_channel(ctrl_url) as channel:
        stub = storage_ctrl_pb2_grpc.CtrlStub(channel)
        request = storage_ctrl_pb2.CTRLDetachVolumeRequest()
        request.volume_id = volume_id
        request.node_id = node_id
        request.target_path = target_path
        stub.CTRLDetachVolume(request)


@volume.command()
@click.argument('volume_id', type=str)
@click.option('--ctrl_url', type=str)
def delete(volume_id, ctrl_url=CTRL_DEFAULT_URL):
    """Delete volume"""
    with grpc.insecure_channel(ctrl_url) as channel:
        stub = storage_ctrl_pb2_grpc.CtrlStub(channel)
        request = storage_ctrl_pb2.CTRLDeleteVolumeRequest()
        request.volume_id = volume_id
        stub.CTRLDeleteVolume(request)


@volume.command(name='list')
@click.option('--ctrl_url', type=str)
def volume_list(ctrl_url=CTRL_DEFAULT_URL):
    """List volumes"""
    with grpc.insecure_channel(ctrl_url) as channel:
        stub = storage_ctrl_pb2_grpc.CtrlStub(channel)
        rsp = stub.CTRLListVolumes(storage_ctrl_pb2.CTRLListVolumesRequest())
        print('VOLUME ID -- CAPACITY -- ADDR -- PORT')
        for entry in rsp.entries:
            print(f"{entry.volume.volume_id} -- ", end="")
            print(f"{entry.volume.capacity_bytes} -- ", end="")
            print(f"{entry.volume.volume_context['addr_traddr']} -- ", end="")
            print(f"{entry.volume.volume_context['addr_trsvcid']}")


@volume.command()
@click.argument('subsystem_nqn', type=str)
@click.argument('node_id', type=str)
@click.argument('pf_index', type=int, required=False)
@click.argument('vf_index', type=int, required=False)
@click.argument('serial_number', type=str, required=False)
@click.argument('model_number', type=str, required=False)
@click.option('--ctrl_url', type=str)
def controller_create(subsystem_nqn, node_id, pf_index, vf_index, serial_number, model_number, ctrl_url=CTRL_DEFAULT_URL):
    """Create a NVMe controller on the DPU"""
    with grpc.insecure_channel(ctrl_url) as channel:
        stub = storage_ctrl_pb2_grpc.CtrlStub(channel)
        request = storage_ctrl_pb2.CTRLCreateControllerRequest()
        request.node_id = node_id
        request.subsystem_nqn = subsystem_nqn

        if pf_index is not None:
            request.pf_index = pf_index

        if vf_index is not None:
            request.vf_index = vf_index

        if serial_number is not None:
            request.serial_number = serial_number

        if model_number is not None:
            request.model_number = model_number

        rsp = stub.CTRLCreateController(request)
        print(rsp)


@volume.command()
@click.argument('controller_id', type=str)
@click.argument('node_id', type=str)
@click.option('--ctrl_url', type=str)
def controller_delete(controller_id, node_id, ctrl_url=CTRL_DEFAULT_URL):
    """Delete a NVMe controller on the DPU"""
    with grpc.insecure_channel(ctrl_url) as channel:
        stub = storage_ctrl_pb2_grpc.CtrlStub(channel)
        request = storage_ctrl_pb2.CTRLDeleteControllerRequest()
        request.controller_id = controller_id
        request.node_id = node_id

        stub.CTRLDeleteController(request)


cli = click.CommandCollection(sources=[volume])


if __name__ == '__main__':
    cli()
