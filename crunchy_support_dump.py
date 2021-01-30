#!/usr/bin/env python3
"""
Copyright 2017 - 2020 Crunchy Data
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Crunchy kubernetes support dump script

Author: Pramodh Mereddy
Email: pramodh.mereddy@crunchydata.com

Description:
    This script collects kubernetes objects, logs and other metadata from
    the objects corresponding to Crunchydata container solution
    NOTE: secrets are data are NOT collected

Pre-requisites:
    1. Valid login session to your kubernetes cluster
    2. kubectl or oc CLI in your PATH

Example:
    $HOME/crunchy/support/crunchy_support_dump.py -n pgdb -o $HOME/dumps/crunchy/pgdb

Arguments:
    -n: namespace or project name
    -o: directory to create the support dump in

"""

from __future__ import print_function
from shutil import rmtree
import argparse
import logging
import os
import subprocess
import sys
import tarfile
import posixpath
import time
from collections import OrderedDict

if sys.version_info[0] < 3:
    print("Python 3 or a more recent version is required.")
    exit()


class Options(object):
    """
        class for globals
    """
    def __init__(self, output_dir, namespace, kube_cli):
        self.output_dir = output_dir
        self.namespace = namespace
        self.kube_cli = kube_cli
        self.dir_name = "crunchy_k8s_support_dump_{}".format(time.strftime("%Y%m%d-%H%M%S"))

OPT = Options("", "", "kubectl")

MAX_ARCHIVE_EMAIL_SIZE = 25*1024*1024
logger = logging.getLogger("crunchy_support")  # pylint: disable=locally-disabled, invalid-name

API_RESOURCES = [
    "pods",
    "ReplicaSet",
    "Deployment",
    "Services",
    "Routes",
    "Ingress",
    "NetworkPolicies",
    "pvc",
    "configmap",
    "pgreplicas",
    "pgclusters",
    "pgpolicies",
    "pgtasks"
]

CONTAINER_COMMANDS = {
    'collect' : [],
    'database' : ["patronictl list", "patronictl history"],
    'pgbadger' : [],
    'all' : ["ps aux --width 500", "df -h", "env"]
}

def run():
    """
        Main function to collect support dump
    """

    if OPT.output_dir:
        OPT.output_dir = posixpath.join(OPT.output_dir, OPT.dir_name)
    else:
        OPT.output_dir = posixpath.join(posixpath.abspath(__file__), OPT.dir_name)

    try:
        os.makedirs(OPT.output_dir)
    except OSError as error:
        print(error)

    logger.info("Saving support dump files in %s", OPT.output_dir)

    collect_kube_version()
    collect_node_info()
    collect_namespace_info()
    collect_events()
    collect_pvc_list()
    collect_configmap_list()
    collect_api_resources()
    collect_pg_logs()
    collect_pods_logs()
    collect_pg_pod_details()
    archive_files()


def collect_kube_version():
    """
        function to gather kubernetes version information
    """
    cmd = OPT.kube_cli + " version "
    logger.debug("collecting kube version info: %s", cmd)
    collect_helper(cmd, file_name="version.info", resource_name="version-info")

def collect_node_info():
    """
        function to gather kubernetes node information
    """
    cmd = OPT.kube_cli + " get nodes -o wide "
    logger.debug("collecting node info: %s", cmd)
    collect_helper(cmd, file_name="nodes.info", resource_name="node-info")

def collect_namespace_info():
    """
        function to gather kubernetes namespace information
    """
    if OPT.kube_cli == "oc":
        cmd = OPT.kube_cli + " describe project " + OPT.namespace
    else:
        cmd = OPT.kube_cli + " get namespace -o yaml " + OPT.namespace

    logger.debug("collecting namespace info: %s", cmd)
    collect_helper(cmd, file_name="namespace.info", resource_name="namespace-info")

def collect_pvc_list():
    """
        function to gather kubernetes PVC information
    """
    cmd = OPT.kube_cli + " get pvc"
    collect_helper(cmd, file_name="pvc.list", resource_name="pvc-list")

def collect_pvc_details():
    """
        function to gather kubernetes PVC details
    """
    cmd = OPT.kube_cli + " get pvc -o yaml"
    collect_helper(cmd, file_name="pvc.details", resource_name="pvc-details")

def collect_configmap_list():
    """
        function to gather configmap list
    """
    cmd = OPT.kube_cli + " get configmap"
    collect_helper(cmd, file_name="configmap.list", resource_name="configmap-list")

def collect_configmap_details():
    """
        function to gather configmap details
    """
    cmd = OPT.kube_cli + " get configmap -o yaml"
    collect_helper(cmd, file_name="configmap.details", resource_name="configmap-details")

def collect_events():
    """
        function to gather k8s events
    """
    cmd = OPT.kube_cli + " get events {}".format(get_namespace_argument())
    collect_helper(cmd=cmd, file_name="events", resource_name="k8s events")

def collect_api_resources():
    """
        function to gather details on different k8s resources
    """
    logger.info("Collecting API resources:")
    resources_out = OrderedDict()
    for resource in API_RESOURCES:
        if OPT.kube_cli == "kubectl" and resource == "Routes":
            continue
        output = run_kube_get(resource)
        if output:
            resources_out[resource] = run_kube_get(resource)
            logger.info("  + %s", resource)

    for entry, out in resources_out.items():
        with open(posixpath.join(OPT.output_dir, entry), "wb") as file_pointer:
            file_pointer.write(out)


def collect_pods_logs():
    """
        Collects all the pods logs from a given namespace
    """
    logger.info("Collecting pod logs:")
    logs_dir = posixpath.join(OPT.output_dir, "pod_logs")
    os.makedirs(logs_dir)

    pods = get_pods()
    if not pods:
        logger.warning("Could not get pods list - skipping pods logs collection")
        return

    for pod in pods:
        containers = get_containers(pod)
        for cont in containers:
            container = cont.rstrip()
            cmd = OPT.kube_cli + " logs {} {} -c {}". \
                format(get_namespace_argument(), pod, container)
            with open("{}/{}_{}.log".format(logs_dir, pod, container), "wb") as file_pointer:
                handle = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, \
                    stderr=subprocess.STDOUT)
                while True:
                    line = handle.stdout.readline()
                    if line:
                        file_pointer.write(line)
                    else:
                        break
            logger.info("  + pod:%s, container:%s", pod, container)


def collect_pg_pod_details():
    """
        Collects PG pods details
    """
    logger.info("Collecting PG pod details:")
    logs_dir = posixpath.join(OPT.output_dir, "pg_pod_details")
    os.makedirs(logs_dir)

    pods = get_pg_pods()
    if not pods:
        logger.warning("Could not get pods list - skipping PG pod details collection")
        return

    for pod in pods:
        containers = get_containers(pod)
        for cont in containers:
            container = cont.rstrip()
            with open("{}/{}_{}.log".format(logs_dir, pod, container), "ab+") as file_pointer:
                for command in CONTAINER_COMMANDS['all']+CONTAINER_COMMANDS[container]:
                    cmd = OPT.kube_cli + " exec -it {} -c {} {} -- /bin/bash -c '{}'" \
                       .format(get_namespace_argument(), container, pod, command)
                    handle = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, \
                        stderr=subprocess.STDOUT)
                    while True:
                        line = handle.stdout.readline()
                        if line:
                            file_pointer.write(line)
                        else:
                            break
            logger.info("  + pod:%s, container:%s", pod, container)


def collect_pg_logs():
    """
        Collects PG database server logs
    """
    logger.info("Collecting last 2 PG logs (This could take a while)")
    logs_dir = posixpath.join(OPT.output_dir, "pg_logs")
    os.makedirs(logs_dir)
    pods = get_pg_pods()
    if not pods:
        logger.warning("Could not get pods list - skipping pods logs collection")
        return

    for pod in pods:
        tgt_file = "{}/{}".format(logs_dir, pod)
        os.makedirs(tgt_file)
        cmd = OPT.kube_cli + \
            " exec -it {} -c database {} -- /bin/bash -c 'ls -d /pgdata/*/pg_log/* | head -2'" \
           .format(get_namespace_argument(), pod)
        handle = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        while True:
            line = handle.stdout.readline()
            if line:
                cmd = OPT.kube_cli + \
                    " cp -c database {} {}:{} {}" \
                    .format(get_namespace_argument(), pod, line.rstrip().decode('UTF-8'), tgt_file)
                handle2 = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, \
                    stderr=subprocess.STDOUT)
                handle2.wait()
            else:
                break
        logger.info("  + pod:%s", pod)


def archive_files():
    """
        Create an archive and compress it
    """
    archive_file_size = 0
    file_name = OPT.output_dir + ".tar.gz"

    with tarfile.open(file_name, "w|gz") as tar:
        tar.add(OPT.output_dir, arcname=OPT.dir_name)
    logger.info("Archive file : %s ", file_name)

    # Let user delete the files manually

    #return_code, out = run_shell_command("rm -rf {}".format(OPT.output_dir))
    #if return_code:
    #    logger.warning('Failed to delete directory after archiving: %s', out)
    #logger.info("support dump files saved at %s", OPT.output_dir)
    try:
        archive_file_size = os.stat(file_name).st_size
        logger.info("------------------------------------------------------------------------")
        if archive_file_size > MAX_ARCHIVE_EMAIL_SIZE:
            logger.info("Archive file (%d bytes) may be too big to email.", archive_file_size)
            logger.info("Please request file share link by emailing support@crunchydata.com")
        else:
            logger.info("Archive file size (bytes): %s ", archive_file_size)
            logger.info("Email the support dump to support@crunchydata.com")
        logger.info("------------------------------------------------------------------------")
    except Exception as _:
        logger.warning("Archive file size: NA")


def get_pods():
    """
        Returns list of pods names
    """
    cmd = OPT.kube_cli + \
        " get pod {} -lvendor=crunchydata -o=custom-columns=NAME:.metadata.name --no-headers" \
       .format(get_namespace_argument())
    return_code, out = run_shell_command(cmd)
    if return_code == 0:
        return out.decode("utf-8").split("\n")[:-1]
    logger.warning("Failed to get pods: %s", out)
    return None


def get_pg_pods():
    """
        Returns list of pods names
    """
    cmd = OPT.kube_cli + " get pod {} -lpgo-pg-database=true,vendor=crunchydata \
        -o=custom-columns=NAME:.metadata.name --no-headers".format(get_namespace_argument())
    return_code, out = run_shell_command(cmd)
    if return_code == 0:
        return out.decode("utf-8").split("\n")[:-1]
    logger.warning("Failed to get pods: %s", out)
    return None


def get_containers(pod_name):
    """
        Returns list of containers in a pod
    """
    cmd = OPT.kube_cli + \
        " get pods {} {} --no-headers -o=custom-columns=CONTAINERS:.spec.containers[*].name" \
        .format(get_namespace_argument(), pod_name)
    return_code, out = run_shell_command(cmd)
    if return_code == 0:
        return out.decode("utf-8").split(",")
    logger.warning("Failed to get pods: %s", out)
    return None


def get_namespace_argument():
    """
        Returns namespace option for kube cli
    """
    if OPT.namespace:
        return "-n {}".format(OPT.namespace)
    return ""


def collect_helper(cmd, file_name, resource_name):
    """
        helper function to gather data
    """
    return_code, out = run_shell_command(cmd)
    if return_code:
        logger.warning("Error when running %s: %s", cmd, out)
        return
    path = posixpath.join(OPT.output_dir, file_name)
    with open(path, "wb") as file_pointer:
        file_pointer.write(out)
    logger.info("Collected %s", resource_name)


def run_shell_command(cmd, log_error=True):
    """
        Returns a tuple of the shell exit code, output
    """
    try:
        output = subprocess.check_output(
            cmd,
            shell=True,
            stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as ex:
        if log_error:
            logger.warning("Failed in shell command: %s, output: %s", cmd, ex.output)
        return ex.returncode, ex.output

    return 0, output


def run_kube_get(resource_type):
    """
        Returns a tuple of the shell exit code, and kube cli get output
    """
    cmd = OPT.kube_cli + " get {} {} -o yaml".format(resource_type, get_namespace_argument())
    return_code, out = run_shell_command(cmd)
    if return_code == 0:
        return out
    logger.warning("Failed to get %s resource: %s", resource_type, out)
    return None


def get_kube_cli():
    """
        Determine which kube CLI to use
    """
    cmd = "which oc"
    return_code, _ = run_shell_command(cmd, False)
    if return_code == 0:
        return "oc"

    cmd = "which kubectl"
    return_code, _ = run_shell_command(cmd, False)
    if return_code == 0:
        return "kubectl"
    else:
        logger.error("kubernetes CLI not found")
        sys.exit()


def check_kube_access():
    """
        Check if the user has access to kube cluster
    """
    if OPT.kube_cli == "oc":
        cmd = "oc whoami"
    else:
        cmd = "kubectl cluster-info"

    return_code, _ = run_shell_command(cmd)
    return return_code


if __name__ == "__main__":
    logger.setLevel(logging.INFO)
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s')
    parser = argparse.ArgumentParser(description='Crunchy support dump collector', add_help=True)  # pylint: disable=locally-disabled, invalid-name
    requiredNamed = parser.add_argument_group('required arguments') # pylint: disable=locally-disabled, invalid-name
    requiredNamed.add_argument('-n', '--namespace', required=True, action="store", type=str, \
        help='kubernetes namespace to use to create crunchy support dump')
    requiredNamed.add_argument('-o', '--output_dir', required=True, action="store", type=str, \
        help='path to use for support dump archive')
    results = parser.parse_args()  # pylint: disable=locally-disabled, invalid-name
    logger.info("------------------------------------------------------------------------------")
    logger.info("Crunchy support dump collector")
    logger.info("NOTE: We gather metadata and pod logs only. (No data and k8s secrets)")
    logger.info("------------------------------------------------------------------------------")
    OPT.namespace = results.namespace
    OPT.kube_cli = get_kube_cli()
    OPT.output_dir = results.output_dir
    if check_kube_access() != 0:
        logger.error("Not connected to kubernetes cluster")
        sys.exit()
    run()
