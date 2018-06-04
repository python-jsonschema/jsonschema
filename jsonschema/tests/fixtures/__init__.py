from pathlib import Path
from json import loads

apple = loads(open(str(Path(__file__).parents[0]) + '/apple.json').read())
orange = loads(open(str(Path(__file__).parents[0]) + '/orange.json').read())
tree = loads(open(str(Path(__file__).parents[0]) + '/tree.json').read())
