"""
  Copyright (c) 2021 International Business Machines
  All rights reserved.
  SPDX-License-Identifier: Apache-2.0
"""
import importlib
from .log import logger
from .generated import storage_pb2_grpc, storage_pb2


class DPUStorageService(storage_pb2_grpc.StorageServicer):

    def __init__(self, dpu: str = 'sofa_storage.dpu_plugin_linux'):
        logger.info('Using DPU plugin: %s', dpu)
        self._dpu = importlib.import_module(dpu, ".").DPU()

    def DPUPublishVolume(self, request, context):
        volume_id = request.volume_id
        volume_context = request.volume_context
        controller_id = request.controller_id
        # network = request.network
        target_path = request.target_path
        secrets = request.secrets

        self._dpu.publishVolume(volume_id, volume_context, controller_id, target_path, secrets)
        return storage_pb2.DPUPublishVolumeResponse()

    def DPUUnpublishVolume(self, request, context):
        volume_id = request.volume_id
        target_path = request.target_path
        self._dpu.unpublishVolume(volume_id, target_path)
        return storage_pb2.DPUUnpublishVolumeResponse()

    def DPUGetInfo(self, request, context):
        info = self._dpu.getInfo()
        return storage_pb2.DPUGetInfoResponse(dpu_type=info['dpu_type'])

    def DPUCreateController(self, request, context):
        subsystem_nqn = request.subsystem_nqn

        pf_index = None
        vf_index = None
        serial_number = None
        model_number = None

        if request.HasField('pf_index'):
            pf_index = request.pf_index

        if request.HasField('vf_index'):
            vf_index = request.vf_index

        if request.HasField('serial_number'):
            serial_number = request.serial_number

        if request.HasField('model_number'):
            model_number = request.model_number

        controller_id = self._dpu.createController(subsystem_nqn, pf_index, vf_index, serial_number, model_number)

        rsp = storage_pb2.DPUCreateControllerResponse()
        rsp.controller_id = controller_id
        return rsp

    def DPUDeleteController(self, request, context):
        controller_id = request.controller_id

        self._dpu.deleteController(controller_id)

        return storage_pb2.DPUDeleteControllerResponse()
