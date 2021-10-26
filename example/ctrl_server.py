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
from .generated import storage_ctrl_pb2_grpc
from .ctrl_service import ControlService


class Server:

    @staticmethod
    def run():
        with futures.ThreadPoolExecutor(max_workers=config['CTRL_SERVER_MAX_WORKERS']) as thread_pool:
            server = grpc.server(thread_pool)
            storage_ctrl_pb2_grpc.add_CtrlServicer_to_server(ControlService(), server)
            server.add_insecure_port(config['CTRL_SERVER_URL'])
            server.start()

            def handle_sigterm(*_):
                logger.info("Received shutdown signal")
                all_rpcs_done_event = server.stop(30)
                all_rpcs_done_event.wait(30)
                logger.info("Shut down gracefully")
            signal(SIGTERM, handle_sigterm)
            signal(SIGINT, handle_sigterm)
            logger.info('Control Server listening on %s', config['CTRL_SERVER_URL'])
            server.wait_for_termination()


if __name__ == '__main__':
    Server.run()
