#!/usr/bin/env python3

from multiprocessing import Pool
import os
import tqdm
import subprocess
import shutil
import time
import random

start = time.time()
test_mode = os.environ["FUZZ_MODE"]
corpus_dir = "/data/zyw/corpus"
distilled_corpus_dir = "/data/zyw/corpus-distilled/csmith-o3"
selected_corpus_dir = distilled_corpus_dir if test_mode == "quickfuzz" else corpus_dir
corpus_items = (
    open(
        os.path.join(
            selected_corpus_dir,
            "index.txt",
        )
    )
    .read()
    .splitlines()
)
baseline = 80000  # tests/hour
test_count_map = {
    "quickfuzz": 10000,
    "fuzz": baseline,
    "fuzz2h": baseline * 2,
    "fuzz4h": baseline * 4,
    "fuzz6h": baseline * 6,
    "fuzz8h": baseline * 8,
    "fuzz10h": baseline * 10,
    "fuzz12h": baseline * 12,
    "fuzz14h": baseline * 14,
    "fuzz16h": baseline * 16,
}
if test_mode not in test_count_map:
    print("Invalid FUZZ_MODE {}".format(test_mode))
    exit(0)
test_count = test_count_map[test_mode]
csmith_dir = "/data/zyw/csmith-install"
common_opts = (
    "-Wno-narrowing -DNDEBUG -g0 -ffp-contract=on -w -mllvm -no-stack-coloring -mllvm -inline-threshold=100000 -I"
    + csmith_dir
    + "/include "
)
gcc_command = "./llvm-build/bin/clang -x c -O0 " + common_opts
clang_command = "./llvm-build/bin/clang -x c " + common_opts
clang_arch_list = [
    ("O1", "-O1"),
    ("O3", "-O3"),
]
exec_qemu_timeout = 30.0
comp_timeout = 30.0
cwd = None

env = os.environ.copy()
env["LLVM_DISABLE_CRASH_REPORT"] = "1"
env["LLVM_DISABLE_SYMBOLIZATION"] = "1"


def build_and_run(arch, basename, file_c, ref_output):
    config, additional_opt = arch
    file_out = basename + "_" + config

    try:
        comp_command = clang_command + additional_opt + " -o " + file_out + " " + file_c
        subprocess.check_call(
            comp_command.split(" "),
            timeout=comp_timeout * 10,
            env=env,
        )
    except subprocess.SubprocessError:
        with open(file_out + "_comp.sh", "w") as f:
            f.write(comp_command)
        return False

    try:
        out = subprocess.check_output([file_out], timeout=exec_qemu_timeout)
    except subprocess.TimeoutExpired:
        # ignore timeout
        os.remove(file_out)
        return True
    except subprocess.SubprocessError:
        with open(file_out + "_run.sh", "w") as f:
            f.write(file_out)
        return False

    if ref_output in out.decode("utf-8"):
        os.remove(file_out)
        return True
    else:
        with open(file_out + "_run.sh", "w") as f:
            f.write(file_out)
        return False


def csmith_test(item: str):
    basename = cwd + "/" + item
    file_c = selected_corpus_dir + "/" + item
    ref_output = item[item.find(".c.") + 3 :]

    result = True
    for arch in clang_arch_list:
        if not build_and_run(arch, basename, file_c, ref_output):
            result = False

    return result


cwd = "./csmith_work"
if os.path.exists(cwd):
    shutil.rmtree(cwd)
os.makedirs(cwd)

if test_mode == "quickfuzz":
    tasks = corpus_items
else:
    tasks = random.sample(corpus_items, test_count)
progress = tqdm.tqdm(tasks, ncols=70, miniters=100, mininterval=60.0)
error_count = 0
skipped_count = 0

pool = Pool(processes=os.cpu_count())

for res in pool.imap_unordered(csmith_test, tasks):
    if res is not None:
        error_count += 0 if res else 1
    else:
        skipped_count += 1
    progress.update(1)
    # progress.set_description("Failed: {} Skipped: {}".format(error_count, skipped_count))
progress.close()

end = time.time()

with open("issue.md", "w") as f:
    f.write(
        "Baseline: https://github.com/llvm/llvm-project/commit/{}\n".format(
            os.environ["LLVM_REVISION"]
        )
    )
    f.write("Patch URL: {}\n".format(os.environ["COMMIT_URL"]))
    f.write("Patch SHA256: {}\n".format(os.environ["PATCH_SHA256"]))
    f.write("Fuzz mode: {}\n".format(test_mode))
    f.write(
        "Total: {} Failed: {} Skipped: {}\n".format(
            len(tasks), error_count, skipped_count
        )
    )
    f.write("Time: {}\n".format(time.strftime("%H:%M:%S", time.gmtime(end - start))))

exit(1 if error_count != 0 else 0)
