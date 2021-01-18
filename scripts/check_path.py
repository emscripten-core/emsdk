# Given a previous path check that the current path
# contains all the same elements in the same order
# with no elements removed.

import os
import sys

old_path = sys.argv[1].split(os.pathsep)
new_path = os.environ['PATH'].split(os.pathsep)

paths_added = [p for p in new_path if p not in old_path]
paths_preserved = [p for p in new_path if p in old_path]

for p in old_path:
  if p not in paths_preserved:
    print('path not reserved: ' + p)
    sys.exit(1)

# Check that ordering matches too.
if old_path != paths_preserved:
  print('preserved paths don\'t match original path:')
  print('old:')
  for p in old_path:
    print(' - ' + p)
  print('preserved:')
  for p in paths_preserved:
    print(' - ' + p)
  sys.exit(1)
