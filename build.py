#!/usr/bin/env python
#
# Copyright (C) 2015 The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""Builds GDB for Android."""
from __future__ import print_function

import argparse
import inspect
import multiprocessing
import os
import subprocess
import sys


def android_path(path=''):
    top = os.getenv('ANDROID_BUILD_TOP', '')
    if not top:
        sys.exit('ANDROID_BUILD_TOP not set. Cannot continue.\n'
                 'Please set ANDROID_BUILD_TOP to point to the root of an '
                 'Android tree.')
    return os.path.realpath(os.path.join(top, path))


def get_default_package_dir():
    return android_path('out/ndk')


def get_default_host():
    if sys.platform in ('linux', 'linux2'):
        return 'linux'
    elif sys.platform == 'darwin':
        return 'darwin'
    else:
        raise RuntimeError('Unsupported host: {}'.format(sys.platform))


ALL_TOOLCHAINS = (
    'arm-linux-androideabi', 'aarch64-linux-android',
    'mipsel-linux-android', 'mips64el-linux-android',
    'x86', 'x86_64',
)


class ArgParser(argparse.ArgumentParser):
    def __init__(self):
        super(ArgParser, self).__init__(
            description=inspect.getdoc(sys.modules[__name__]),
            formatter_class=argparse.RawDescriptionHelpFormatter)

        self.add_argument(
            '--host', choices=('darwin', 'linux', 'windows', 'windows64'),
            help='Build binaries for given OS (e.g. linux).')
        self.add_argument(
            '--package-dir', help='Directory to place the packaged GCC.',
            default=get_default_package_dir())
        self.add_argument(
            '--toolchain', choices=ALL_TOOLCHAINS,
            help='Toolchain to build. Builds all if not present.')


def toolchain_to_arch(toolchain):
    return {
        'arm-linux-androideabi': 'arm',
        'aarch64-linux-android': 'arm64',
        'mipsel-linux-android': 'mips',
        'mips64el-linux-android': 'mips64',
        'x86': 'x86',
        'x86_64': 'x86_64',
    }[toolchain]


def default_api_level(arch):
    if '64' in arch:
        return 21
    else:
        return 9


def sysroot_path(toolchain):
    arch = toolchain_to_arch(toolchain)
    version = default_api_level(arch)

    prebuilt_ndk = 'prebuilts/ndk/current'
    sysroot_subpath = 'platforms/android-{}/arch-{}'.format(version, arch)
    return android_path(os.path.join(prebuilt_ndk, sysroot_subpath))


def main():
    args = ArgParser().parse_args()

    os.chdir(android_path('toolchain/gdb'))

    toolchain_path = android_path('toolchain')
    ndk_path = android_path('ndk')

    jobs_arg = '-j{}'.format(multiprocessing.cpu_count())

    package_dir_arg = '--package-dir={}'.format(args.package_dir)

    toolchains = ALL_TOOLCHAINS
    if args.toolchain is not None:
        toolchains = [args.toolchain]

    host = args.host
    if host is None:
        host = get_default_host()

    ndk_build_tools_path = android_path('ndk/build/tools')
    build_env = dict(os.environ)
    build_env['NDK_BUILDTOOLS_PATH'] = ndk_build_tools_path
    build_env['ANDROID_NDK_ROOT'] = ndk_path

    print('Building {} gdb: {}'.format(host, ' '.join(toolchains)))
    build_cmd = [
        'bash', 'build-gdb.sh', "--toolchain-src-dir=" + toolchain_path,
        "--ndk-dir=" + ndk_path, '--verbose',
        "--arch=" + ",".join([toolchain_to_arch(tc) for tc in toolchains]),
        package_dir_arg, jobs_arg,
    ]
    print(' '.join(build_cmd))

    subprocess.check_call(build_cmd, env=build_env)

if __name__ == '__main__':
    main()
