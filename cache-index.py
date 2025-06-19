#!/usr/bin/env python3

import os
import sys

corpus_dir = sys.argv[1]
works = list(filter(lambda x: x.count(".c."), os.listdir(corpus_dir)))

index_file = os.path.join(corpus_dir, "index.txt")
with open(index_file, "w") as f:
    for work in works:
        f.write(work + "\n")
print(f"Index file created at {index_file} with {len(works)} entries.")
