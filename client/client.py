"""
Simple client that would run on handheld device used by workers in warehouse
install in this directory with: python -m pip install -e .
"""

import click
import requests

@click.group()
def cli():
    """Inventory Manager Client (IMC)"""


@cli.command()
@click.argument('warehouse_id')
@click.argument('item_name')
def choose_stock(warehouse_id, item_name):
    """List all cataloged APIs."""
    click.echo(f'Choosing stock for {item_name} in warehouse {warehouse_id}')

if __name__ == '__main__':
    cli(prog_name='client')