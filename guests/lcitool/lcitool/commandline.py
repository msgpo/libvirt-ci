# commandline.py - module containing the lcitool command line parser
#
# Copyright (C) 2017-2020 Red Hat, Inc.
#
# SPDX-License-Identifier: GPL-2.0-or-later

import argparse

from lcitool.application import Application


class CommandLine:

    def __init__(self):
        self._parser = argparse.ArgumentParser(
            conflict_handler="resolve",
            description="libvirt CI guest management tool",
        )

        self._parser.add_argument("--debug", action="store_true",
                                  help="display debugging information")

        subparsers = self._parser.add_subparsers(metavar="ACTION")
        subparsers.required = True

        def add_hosts_arg(parser):
            parser.add_argument(
                "hosts",
                help="list of hosts to act on (accepts globs)",
            )

        def add_projects_arg(parser):
            parser.add_argument(
                "projects",
                help="list of projects to consider (accepts globs)",
            )

        def add_gitrev_arg(parser):
            parser.add_argument(
                "-g", "--git-revision",
                help="git revision to build (remote/branch)",
            )

        def add_cross_arch_arg(parser):
            parser.add_argument(
                "-x", "--cross-arch",
                help="target architecture for cross compiler",
            )

        def add_wait_arg(parser):
            parser.add_argument(
                "-w", "--wait",
                help="wait for installation to complete",
                default=False,
                action="store_true",
            )

        installparser = subparsers.add_parser(
            "install", help="perform unattended host installation")
        installparser.set_defaults(func=Application._action_install)

        add_hosts_arg(installparser)
        add_wait_arg(installparser)

        updateparser = subparsers.add_parser(
            "update", help="prepare hosts and keep them updated")
        updateparser.set_defaults(func=Application._action_update)

        add_hosts_arg(updateparser)
        add_projects_arg(updateparser)
        add_gitrev_arg(updateparser)

        buildparser = subparsers.add_parser(
            "build", help="build projects on hosts")
        buildparser.set_defaults(func=Application._action_build)

        add_hosts_arg(buildparser)
        add_projects_arg(buildparser)
        add_gitrev_arg(buildparser)

        hostsparser = subparsers.add_parser(
            "hosts", help="list all known hosts")
        hostsparser.set_defaults(func=Application._action_hosts)

        projectsparser = subparsers.add_parser(
            "projects", help="list all known projects")
        projectsparser.set_defaults(func=Application._action_projects)

        variablesparser = subparsers.add_parser(
            "variables", help="generate variables (doesn't access the host)")
        variablesparser.set_defaults(func=Application._action_variables)

        add_hosts_arg(variablesparser)
        add_projects_arg(variablesparser)
        add_cross_arch_arg(variablesparser)

        dockerfileparser = subparsers.add_parser(
            "dockerfile", help="generate Dockerfile (doesn't access the host)")
        dockerfileparser.set_defaults(func=Application._action_dockerfile)

        add_hosts_arg(dockerfileparser)
        add_projects_arg(dockerfileparser)
        add_cross_arch_arg(dockerfileparser)

    def parse(self):
        return self._parser.parse_args()
