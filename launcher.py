#   python launcher.py                 potato textures, in a window
#   python launcher.py mid             mid / low / medium / high / ultra
#   python launcher.py loud            prints every file it found and every one it did not

import sys
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parent

CANDIDATES = [
    ROOT / 'src' / 'game.py',
    ROOT / 'assets and textures' / 'models for menu and world map' / 'mainNEW.py',
]


def find_game():
    for path in CANDIDATES:
        if path.exists():
            return path
    for path in ROOT.rglob('mainNEW.py'):
        return path
    for path in ROOT.rglob('game.py'):
        return path
    return None


def main():
    # ursina has to be imported HERE, before the game runs. it reads
    # sys.argv[0] the second it is imported and that is where it decides the
    # assets are - right now that is this file, so it comes out as this folder.
    # runpy rewrites sys.argv[0] to the game file, so any later and it would
    # come out as src/ and nothing would have a texture on it, thats what i'm trying to ignore with having this launcher
    try:
        import ursina
    except ImportError:
        print('Ursina is not installed in this environment.\n'
              'Run:  pip install -r requirements.txt')
        return 1

    game = find_game()
    if game is None:
        print('Could not find the game source. Expected one of:')
        for c in CANDIDATES:
            print('   ', c)
        return 1

    print('ETERNAL MALICE AND MERCENARY WORK  ->  %s' % game.relative_to(ROOT))
    runpy.run_path(str(game), run_name='__main__')
    return 0


if __name__ == '__main__':
    sys.exit(main())
