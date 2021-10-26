# pylint: disable=E1101
"""
  Copyright (c) 2021 International Business Machines
  All rights reserved.
  SPDX-License-Identifier: Apache-2.0
"""
import grpc

from sofa_storage.generated import storage_pb2
from sofa_storage.generated import storage_pb2_grpc
from sofa_storage.error import SofaStorageException

from .config import config
from .log import logger
from .error import SofaStorageControlExampleException

from .generated import storage_ctrl_pb2
from .generated import storage_ctrl_pb2_grpc

from . import lvm
from . import nvmet

NODES = config['NODES']


class ControlService(storage_ctrl_pb2_grpc.CtrlServicer):

    def CTRLCreateVolume(self, request, context):
        logger.info('Create Volume, %s, %s', request.name, request.capacity_bytes)
        if request.capacity_bytes > config['MAX_CAPACITY_BYTES']:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details('capacity_bytes is too large')
            return storage_ctrl_pb2.Response()
        try:
            lvm.createVolume(request.name, request.capacity_bytes)
        except SofaStorageControlExampleException:
            context.set_code(grpc.StatusCode.UNKNOWN)
            context.set_details('LVM create volume failed')
            return storage_ctrl_pb2.Response()
        try:
            nvmet.publishVolume(request.name)
        except SofaStorageControlExampleException:
            context.set_code(grpc.StatusCode.UNKNOWN)
            context.set_details('NVMET publish volume failed')
            return storage_ctrl_pb2.Response()

        if request.volume_content_source.volume.volume_id != '':
            logger.info('Populating Volume %s from volume %s', request.name, request.volume_content_source.volume.volume_id)
            lvm.populateVolume(request.name, request.volume_content_source.volume.volume_id)
        return storage_ctrl_pb2.CTRLCreateVolumeResponse()

    def CTRLDeleteVolume(self, request, context):
        logger.info('Delete Volume %s', request.volume_id)
        nvmet.unpublishVolume(request.volume_id)
        lvm.deleteVolume(request.volume_id)
        return storage_ctrl_pb2.CTRLDeleteVolumeResponse()

    def CTRLAttachVolume(self, request, context):
        logger.info('Attach Volume %s', request.volume_id)
        dpu_server_url = NODES[request.node_id]['dpu_server_url']
        dpu_req = storage_pb2.DPUPublishVolumeRequest()
        dpu_req.volume_id = request.volume_id
        dpu_req.controller_id = request.controller_id
        dpu_req.network = request.network
        dpu_req.target_path = request.target_path

        try:
            po = nvmet.Nvmet().getPortBySubsystem(request.volume_id)
            dpu_req.volume_context['addr_adrfam'] = po.addr_adrfam
            dpu_req.volume_context['addr_traddr'] = po.addr_traddr
            dpu_req.volume_context['addr_trsvcid'] = str(po.addr_trsvcid)
        except SofaStorageException:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details('Fetching volume information failed')
            return storage_ctrl_pb2.CTRLAttachVolumeResponse()

        if request.secrets:
            dpu_req.secrets['encryption_key'] = request.secrets['encryption_key']

        with grpc.insecure_channel(dpu_server_url) as channel:
            stub = storage_pb2_grpc.StorageStub(channel)
            stub.DPUPublishVolume(dpu_req)
        return storage_ctrl_pb2.CTRLAttachVolumeResponse()

    def CTRLDetachVolume(self, request, context):
        logger.info('Detach Volume %s', request.volume_id)
        dpu_server_url = NODES[request.node_id]['dpu_server_url']
        dpu_req = storage_pb2.DPUUnpublishVolumeRequest()
        dpu_req.volume_id = request.volume_id
        dpu_req.target_path = request.target_path
        with grpc.insecure_channel(dpu_server_url) as channel:
            stub = storage_pb2_grpc.StorageStub(channel)
            stub.DPUUnpublishVolume(dpu_req)
        return storage_ctrl_pb2.CTRLDetachVolumeResponse()

    def CTRLListVolumes(self, request, context):
        logger.info('List Volumes')
        rsp = storage_ctrl_pb2.CTRLListVolumesResponse()
        try:
            volumes = lvm.listVolumes()
            for volume in volumes:
                rsp_entry = storage_ctrl_pb2.CTRLListVolumesResponse.Entry()
                rsp_entry.volume.capacity_bytes = volume['lv_size']
                rsp_entry.volume.volume_id = volume['lv_name']

                po = nvmet.Nvmet().getPortBySubsystem(rsp_entry.volume.volume_id)
                if po is not None:
                    rsp_entry.volume.volume_context['addr_adrfam'] = po.addr_adrfam
                    rsp_entry.volume.volume_context['addr_traddr'] = po.addr_traddr
                    rsp_entry.volume.volume_context['addr_trsvcid'] = str(po.addr_trsvcid)
                rsp.entries.append(rsp_entry)
        except SofaStorageControlExampleException:
            context.set_code(grpc.StatusCode.UNKNOWN)
            context.set_details('Listing volumes failed')
            return storage_ctrl_pb2.Response()

        return rsp

    def CTRLCreateController(self, request, context):
        logger.info('Create Controller')
        dpu_server_url = NODES[request.node_id]['dpu_server_url']
        logger.info('dpu_server_url: %s', dpu_server_url)

        dpu_req = storage_pb2.DPUCreateControllerRequest()
        dpu_req.subsystem_nqn = request.subsystem_nqn

        if request.HasField('pf_index'):
            dpu_req.pf_index = request.pf_index

        if request.HasField('vf_index'):
            dpu_req.vf_index = request.vf_index

        if request.HasField('serial_number'):
            dpu_req.serial_number = request.serial_number

        if request.HasField('model_number'):
            dpu_req.model_number = request.model_number

        with grpc.insecure_channel(dpu_server_url) as channel:
            stub = storage_pb2_grpc.StorageStub(channel)
            dpu_rsp = stub.DPUCreateController(dpu_req)

        rsp = storage_ctrl_pb2.CTRLCreateControllerResponse()
        rsp.controller_id = dpu_rsp.controller_id

        return rsp

    def CTRLDeleteController(self, request, context):
        logger.info('Delete Controller')
        dpu_server_url = NODES[request.node_id]['dpu_server_url']

        dpu_req = storage_pb2.DPUDeleteControllerRequest()
        dpu_req.controller_id = request.controller_id

        with grpc.insecure_channel(dpu_server_url) as channel:
            stub = storage_pb2_grpc.StorageStub(channel)
            stub.DPUDeleteController(dpu_req)

        return storage_ctrl_pb2.CTRLDeleteControllerResponse()
