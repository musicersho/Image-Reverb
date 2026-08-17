"""入口：python -m src.image_reverb <photo>"""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
