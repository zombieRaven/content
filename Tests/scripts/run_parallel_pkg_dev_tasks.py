#!/usr/bin/env python3
import os
import sys
import subprocess
import concurrent.futures
import yaml
import glob
from typing import List, Optional, Tuple

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONTENT_DIR = os.path.abspath(SCRIPT_DIR + '/../..')
sys.path.append(CONTENT_DIR)
from Tests.test_utils import print_color, LOG_COLORS  # noqa: E402


def run_dev_task(pkg_dir: str, params: Optional[List[str]]) -> Tuple[subprocess.CompletedProcess, str]:
    args = ['demisto-sdk lint', '-d', pkg_dir]
    if params:
        args.extend(params)
    cmd_line = " ".join(args)
    # color stderr in red and remove the warning about no config file from pylint
    cmd_line += r" 2> >(sed '/No config file found, using default configuration/d' | sed $'s,.*,\x1B[31m&\x1B[0m,'>&1)"
    res = subprocess.run(cmd_line, text=True, capture_output=True, shell=True, executable='/bin/bash')
    return res, pkg_dir


def get_yml_paths_in_dir(project_dir: str, error_msg: str,) -> Tuple[list, str]:
    """
    Gets the project directory and returns the path of the first yml file in that directory
    :param project_dir: string path to the project_dir
    :param error_msg: the error msg to show to the user in case not yml files found in the directory
    :return: first returned argument is the list of all yml files paths in the directory, second returned argument is a
    string path to the first yml file in project_dir
    """
    yml_files = glob.glob(os.path.join(project_dir, '*.yml'))
    if not yml_files:
        if error_msg:
            print(error_msg)
        return [], ''
    return yml_files, yml_files[0]


def get_docker_images(script_obj):
    imgs = [script_obj.get('dockerimage') or 'demisto/python:1.3-alpine']
    alt_imgs = script_obj.get('alt_dockerimages')
    if alt_imgs:
        imgs.extend(alt_imgs)
    return imgs


def get_python_version(docker_image):
    """
    Get the python version of a docker image
    Arguments:
        docker_image {string} -- Docker image being used by the project
    Return:
        python version as a float (2.7, 3.7)
    Raises:
        ValueError -- if version is not supported
    """
    stderr_out = -3
    py_ver = subprocess.check_output(["docker", "run", "--rm", docker_image, "python", "-c",
                                      "import sys;print('{}.{}'.format(sys.version_info[0], sys.version_info[1]))"],
                                     universal_newlines=True, stderr=stderr_out).strip()

    py_num = float(py_ver)
    return py_num


def get_image_num(pkg_dir):
    # load yaml
    _, yml_path = get_yml_paths_in_dir(pkg_dir, "No Package Dir Given")
    if not yml_path:
        return 1
    with open(yml_path, 'r') as yml_file:
        yml_data = yaml.safe_load(yml_file)
    script_obj = yml_data
    if isinstance(script_obj.get('script'), dict):
        script_obj = script_obj.get('script')
    script_type = script_obj.get('type')
    if script_type != 'python':
        if script_type == 'powershell':
            # TODO powershell linting
            return 0

    dockers = get_docker_images(script_obj)
    py_num = get_python_version(dockers[0])

    return py_num


def should_run_pkg(pkg_dir: str) -> bool:
    diff_compare = os.getenv("DIFF_COMPARE")
    if not diff_compare:
        return True
    if os.getenv('CONTENT_PRECOMMIT_RUN_DEV_TASKS'):
        # if running in precommit we check against staged
        diff_compare = '--staged'
    res = subprocess.run(["git", "diff", "--name-only", diff_compare, "--", pkg_dir], text=True, capture_output=True)
    if res.stdout:
        return True
    return False


def handle_run_res(res: Tuple[subprocess.CompletedProcess, str], fail_pkgs: list, good_pkgs: list):
    if res[0].returncode != 0:
        fail_pkgs.append(res[1])
        print_color("============= {} =============".format(res[1]), LOG_COLORS.RED)
    else:
        good_pkgs.append(res[1])
        print("============= {} =============".format(res[1]))
    print(res[0].stdout)
    print(res[0].stderr)


def create_failed_unittests_file(failed_unittests):
    """
    Creates a file with failed unittests.
    The file will be read in slack_notifier script - which will send the failed unittests to the content-team channel.
    """
    with open('./Tests/failed_unittests.txt', "w") as failed_unittests_file:
        failed_unittests_file.write('\n'.join(failed_unittests))


def main():
    if len(sys.argv) == 2 and (sys.argv[1] == '-h' or sys.argv[1] == '--help'):
        print("Run pkg_dev_test_tasks.py in parallel. Accepts same parameters as pkg_dev_test_tasks.py.\n"
              "Additionally you can specify the following environment variables:\n"
              "DIFF_COMPARE: specify how to do a git compare. Leave empty to run on all.\n"
              "MAX_WORKERS: max amount of workers to use for running "
              )
        sys.exit(1)
    max_workers = int(os.getenv("MAX_WORKERS", "10"))
    find_out = subprocess.check_output(["find", "Integrations", "Scripts", "Beta_Integrations",
                                        "-maxdepth", "1", "-mindepth", "1", "-type", "d", "-print"], text=True)
    pkg_dirs = find_out.splitlines()
    pkgs_to_run = []
    for dir in pkg_dirs:
        print(dir)
        if should_run_pkg(dir):
            pkgs_to_run.append(dir)
    print("Starting parallel run for [{}] packages with [{}] max workers".format(len(pkgs_to_run), max_workers))
    params = sys.argv[1::]
    fail_pkgs = []
    good_pkgs = []
    # req2 = get_dev_requirements(2.7)
    # req3 = get_dev_requirements(3.7)
    # # run CommonServer non parallel to avoid conflicts
    # # when we modify the file for mypy includes
    # if 'Scripts/CommonServerPython' in pkgs_to_run:
    #     pkgs_to_run.remove('Scripts/CommonServerPython')
    #     res = run_dev_task('Scripts/CommonServerPython', params)
    #     handle_run_res(res, fail_pkgs, good_pkgs)
    # with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
    #     futures_submit = [executor.submit(run_dev_task, dir, params, req3, req2) for dir in pkgs_to_run]
    #     for future in concurrent.futures.as_completed(futures_submit):
    #         res = future.result()
    #         handle_run_res(res, fail_pkgs, good_pkgs)
    for package in pkgs_to_run:
        res_code, _ = run_dev_task(pkg_dir=package, params=params)
        if res_code == 0:
            good_pkgs.append(package)

        else:
            fail_pkgs.append(package)

    create_failed_unittests_file(fail_pkgs)
    if fail_pkgs:
        print_color("\n******* FAIL PKGS: *******", LOG_COLORS.RED)
        print_color("\n\t{}\n".format("\n\t".join(fail_pkgs)), LOG_COLORS.RED)
    if good_pkgs:
        print_color("\n******* SUCCESS PKGS: *******", LOG_COLORS.GREEN)
        print_color("\n\t{}\n".format("\n\t".join(good_pkgs)), LOG_COLORS.GREEN)
    if not good_pkgs and not fail_pkgs:
        print_color("\n******* No changed packages found *******\n", LOG_COLORS.YELLOW)
    if fail_pkgs:
        sys.exit(1)


if __name__ == "__main__":
    main()
