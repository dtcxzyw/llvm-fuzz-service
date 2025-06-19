#!/usr/bin/env python3


from multiprocessing import Pool
import os
import tqdm
import subprocess
import sys

csmith_dir = sys.argv[1]
corpus_dir = sys.argv[2]
llvm_build = sys.argv[3]
common_opts = (
    "-Wno-narrowing -DNDEBUG -g0 -ffp-contract=on -w -mllvm -no-stack-coloring -I"
    + csmith_dir
    + "/include "
)
gcc_command = llvm_build + "/bin/clang -O0 " + common_opts
exec_timeout = 3.0
comp_timeout = 3.0


def csmith_test(test):
    file_c = corpus_dir + "/" + test
    file_ref = file_c + ".out"
    try:
        subprocess.check_call(
            (gcc_command + "-o " + file_ref + " " + file_c).split(" "),
            timeout=comp_timeout,
        )
    except subprocess.SubprocessError:
        os.remove(file_c)
        return

    try:
        ref_output = subprocess.check_output(file_ref, timeout=exec_timeout)
    except subprocess.SubprocessError:
        os.remove(file_c)
        os.remove(file_ref)
        return

    os.rename(
        file_c,
        file_c + "." + ref_output.decode("utf-8").strip().removeprefix("checksum = "),
    )
    os.remove(file_ref)


works = list(filter(lambda x: x.endswith(".c"), os.listdir(corpus_dir)))

progress = tqdm.tqdm(range(len(works)), ncols=70, miniters=100, mininterval=60.0)
pool = Pool(processes=os.cpu_count())

for res in pool.imap_unordered(csmith_test, works):
    progress.update(1)
progress.close()
