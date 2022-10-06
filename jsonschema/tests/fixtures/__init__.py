from json import loads
from pathlib import Path

apple = loads(open(str(Path(__file__).parents[0]) + '/apple.json').read())
orange = loads(open(str(Path(__file__).parents[0]) + '/orange.json').read())
tree = loads(open(str(Path(__file__).parents[0]) + '/tree.json').read())
