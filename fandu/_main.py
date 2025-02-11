import click

from fandu.utils import test_function


@click.group()
def cli():
    """A simple CLI for working with shapefiles."""
    pass

@cli.command()
def dummy():
    """ dummy test function """
    click.echo( test_function() )


@cli.command()
@click.argument("shapefile", type=click.Path(exists=True))
def plot(shapefile):
    """Plot the given shapefile."""
    click.echo(f"Plotting shapefile: {shapefile}")

@cli.command()
@click.argument("shapefile1", type=click.Path(exists=True))
@click.argument("shapefile2", type=click.Path(exists=True))
@click.option("--output", type=click.Path(), default="merged_output.shp", help="Output shapefile path")
def merge(shapefile1, shapefile2, output):
    """Merge two shapefiles."""
    click.echo(f"Merging {shapefile1} and {shapefile2} into {output}")

if __name__ == "__main__":
    cli()
