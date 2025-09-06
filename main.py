#!/usr/bin/env python3
"""
Input Link - Main entry point

This provides a unified entry point for both sender and receiver applications.
Usage:
  python main.py sender [options]    # Run sender application
  python main.py receiver [options]  # Run receiver application
"""

import sys
import click

from src.input_link.apps.sender import main as sender_main
from src.input_link.apps.receiver import main as receiver_main
from src.input_link.gui.application import run_gui_application


@click.group(invoke_without_command=True)
@click.option('--version', '-v', is_flag=True, help='Show version information')
@click.pass_context
def main(ctx, version):
    """Input Link - Network Controller Forwarding System
    
    Forward controller inputs from sender PC to receiver PC over WebSocket.
    
    Examples:
        python main.py sender --host 192.168.1.100
        python main.py receiver --port 8765 --max-controllers 8
    """
    if version:
        from src.input_link import __version__
        click.echo(f"Input Link v{__version__}")
        return
        
    if ctx.invoked_subcommand is None:
        click.echo("Input Link - Network Controller Forwarding System")
        click.echo()
        click.echo("Usage:")
        click.echo("  python main.py gui                 # Run GUI application")
        click.echo("  python main.py sender [OPTIONS]    # Run sender (captures inputs)")
        click.echo("  python main.py receiver [OPTIONS]  # Run receiver (simulates inputs)")
        click.echo()
        click.echo("For detailed help:")
        click.echo("  python main.py gui --help")
        click.echo("  python main.py sender --help")
        click.echo("  python main.py receiver --help")
        click.echo("  python main.py --version")


@main.command()
@click.option(
    '--config', 
    type=click.Path(exists=False),
    help='Path to configuration file'
)
@click.option(
    '--host',
    default="127.0.0.1",
    help='Receiver host address'
)
@click.option(
    '--port',
    default=8765,
    type=int,
    help='Receiver port'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Enable verbose logging'
)
def sender(config, host, port, verbose):
    """Run Input Link Sender (captures controller inputs)"""
    # Prepare arguments for sender main
    args = []
    if config:
        args.extend(['--config', config])
    if host != "127.0.0.1":
        args.extend(['--host', host])
    if port != 8765:
        args.extend(['--port', str(port)])
    if verbose:
        args.append('--verbose')
    
    # Call sender main with sys.argv override
    original_argv = sys.argv
    try:
        sys.argv = ['input-link-sender'] + args
        sender_main(standalone_mode=False)
    finally:
        sys.argv = original_argv


@main.command()
@click.option(
    '--config',
    type=click.Path(exists=False),
    help='Path to configuration file'
)
@click.option(
    '--port',
    default=8765,
    type=int,
    help='Server port to listen on'
)
@click.option(
    '--max-controllers',
    default=4,
    type=int,
    help='Maximum number of virtual controllers'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Enable verbose logging'
)
def receiver(config, port, max_controllers, verbose):
    """Run Input Link Receiver (simulates controller inputs)"""
    # Prepare arguments for receiver main
    args = []
    if config:
        args.extend(['--config', config])
    if port != 8765:
        args.extend(['--port', str(port)])
    if max_controllers != 4:
        args.extend(['--max-controllers', str(max_controllers)])
    if verbose:
        args.append('--verbose')
    
    # Call receiver main with sys.argv override
    original_argv = sys.argv
    try:
        sys.argv = ['input-link-receiver'] + args
        receiver_main(standalone_mode=False)
    finally:
        sys.argv = original_argv


@main.command()
def gui():
    """Run Input Link GUI Application"""
    try:
        sys.exit(run_gui_application())
    except ImportError as e:
        click.echo(f"GUI dependencies not available: {e}", err=True)
        click.echo("Please install GUI dependencies with: pip install PySide6", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"GUI application error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()