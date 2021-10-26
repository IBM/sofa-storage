"""
  Copyright (c) 2021 International Business Machines
  All rights reserved.
  SPDX-License-Identifier: Apache-2.0
"""
from concurrent import futures
from signal import signal, SIGTERM, SIGINT

import grpc

from .config import config
from .log import logger
from .generated import storage_pb2_grpc
from .dpu_storage_service import DPUStorageService


class DPUServer:

    @staticmethod
    def run():
        with futures.ThreadPoolExecutor(max_workers=config['DPU_SERVER_MAX_WORKERS']) as thread_pool:
            server = grpc.server(thread_pool)
            storage_pb2_grpc.add_StorageServicer_to_server(DPUStorageService(dpu=config['DPU_PLUGIN']), server)
            server.add_insecure_port(config['DPU_SERVER_URL'])
            server.start()

            def handle_sigterm(*_):
                logger.info("Received shutdown signal")
                all_rpcs_done_event = server.stop(30)
                all_rpcs_done_event.wait(30)
                logger.info("Shut down gracefully")
            signal(SIGTERM, handle_sigterm)
            signal(SIGINT, handle_sigterm)
            logger.info('DPU Server listening on %s', config['DPU_SERVER_URL'])
            server.wait_for_termination()


if __name__ == '__main__':
    DPUServer.run()
