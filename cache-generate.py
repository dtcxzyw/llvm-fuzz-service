#!/usr/bin/env python3

from multiprocessing import Pool
import os
import tqdm
import subprocess
import sys

csmith_dir = sys.argv[1]
dst_dir = sys.argv[2]
test_count = int(sys.argv[3])
csmith_command = csmith_dir +"/bin/csmith --max-array-dim 2 --max-array-len-per-dim 4 --max-struct-fields 4 --concise --quiet --builtins --no-packed-struct --no-unions --no-bitfields --no-volatiles --no-volatile-pointers --output "

def csmith_test(i):
    basename = dst_dir+"/test"+str(i)
    file_c = basename + ".c"
    try:
        subprocess.check_call((csmith_command+file_c).split(' '))
    except subprocess.SubprocessError:
        return

    return


os.makedirs(dst_dir)

L = list(range(test_count))
progress = tqdm.tqdm(L, ncols=70, miniters=100, mininterval=60.0)
pool = Pool(processes=os.cpu_count())

for res in pool.imap_unordered(csmith_test, L):
    progress.update(1)
progress.close()
