# Copyright (c) 2025 Biasware LLC
# Proprietary and Confidential. All Rights Reserved.
# This file is the sole property of Biasware LLC.
# Unauthorized use, distribution, or reverse engineering is prohibited.

"""(Deprecated) Wrapper retained for backward compatibility.

This script has been renamed to `db_admin.py` which now supports actions:
    * bootstrap (existing behavior)
    * purge (schema-only drop of videos table) with --force

Please update any references to use:  python ops/db_admin.py --help
"""

import sys

from ops import db_admin

if __name__ == "__main__":  # pragma: no cover
    print(
        "[DEPRECATED] Use 'python ops/db_admin.py --action bootstrap' (or purge). Forwarding...",
        file=sys.stderr,
    )
    sys.exit(db_admin.main())
