import click
import os


@click.group(invoke_without_command=True)
def main():
    pass


@main.command()
def makerequirements():
    os.system("pipenv requirements > requirements.txt")


if __name__ == "__main__":
    main()
