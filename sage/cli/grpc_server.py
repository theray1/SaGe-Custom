# grpc_server.py
# Author: Thomas MINIER - MIT License 2017-2020
import signal
import click
import uvloop

from asyncio import set_event_loop_policy

from sage.grpc.grpc_server import get_server


def stop_server(server, grace=None):
  """Stop server on a CTRL-C event"""
  def __fn__(signum, frame):
    server.stop(grace)
  return __fn__


@click.command()
@click.argument("config")
@click.option(
    "-p", "--port", type=click.INT, default=8000, show_default=True,
    help="The port to bind"
)
@click.option(
    "-w", "--workers", type=click.INT, default=4, show_default=True,
    help="he number of server workers"
)
@click.option(
    "--log-level", type=click.Choice(["debug", "info", "warning", "error"]),
    default="info", show_default=True, help="The granularity of log outputs"
)
def start_grpc_server(config: str, port: int, workers: int, log_level: str) -> None:
  """Launch the Sage gRPC server using the CONFIG configuration file"""
  # Enable uvloop
  set_event_loop_policy(uvloop.EventLoopPolicy())

  server = get_server(config, port=port, workers=workers)
  # Stop the server on a CTRL-C event
  signal.signal(signal.SIGINT, stop_server(server))

  # Start the server, and wait until it completes
  server.start()
  server.wait_for_termination()
