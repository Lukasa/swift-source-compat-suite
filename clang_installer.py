#!/usr/bin/env python
# ===--- clang_installer.py --------------------------------------------------------===
#
#  This source file is part of the Swift.org open source project
#
#  Copyright (c) 2021 Apple Inc. and the Swift project authors
#  Licensed under Apache License v2.0 with Runtime Library Exception
#
#  See https://swift.org/LICENSE.txt for license information
#  See https://swift.org/CONTRIBUTORS.txt for the list of Swift project authors
#
# ===----------------------------------------------------------------------===

import common
import os
import signal

class ClangInstaller(object):
    def __init__(self, prebuilt):
        self.clang_paths = []
        for sdk in ['macosx']:
            try:
                sdk_clang_path = common.check_execute_output(['xcrun', '--sdk', sdk, '--find', 'clang']).strip()
            except:
                pass
            else:
                self.clang_paths.append(sdk_clang_path)

        self.local_clang_path = prebuilt
        self.root_path = common.private_workspace('project_cache')
        self.source_path = os.path.join(self.root_path, 'llvm-project')

        self._default_sig_handlers = {
            signal.SIGINT: signal.getsignal(signal.SIGINT),
            signal.SIGTSTP: signal.getsignal(signal.SIGTSTP)
        }

        def exit_handler(signal_received, frame):
            self.clear()
            default_sig_handler = self._default_sig_handlers[signal_received]
            signal.signal(signal_received, default_sig_handler)
            default_sig_handler(signal_received, frame)

        # run exit_handler() function when CTRL-C or CTRL-Z is received
        signal.signal(signal.SIGINT, exit_handler)
        signal.signal(signal.SIGTSTP, exit_handler)

    @staticmethod
    def orig_postfix():
        return ".compatsuite.orig"

    def install(self):
        for clang_path in self.clang_paths:
            clang_orig_path = clang_path + self.orig_postfix()
            if os.path.isfile(clang_orig_path):
                if os.path.islink(clang_path):
                    common.check_execute(['rm', clang_path])
                elif os.path.isfile(clang_path):
                    continue
            else:
                common.check_execute(['mv', clang_path, clang_orig_path])

            common.check_execute(['ln', '-s', self.local_clang_path, clang_path])

    def clear(self):
        if not self.clang_paths:
            return
        print('Restoring swapped clang binaries.')
        for clang_path in self.clang_paths:
            clang_orig_path = clang_path + self.orig_postfix()
            if not os.path.isfile(clang_orig_path):
                continue

            if os.path.isfile(clang_path):
                if os.path.islink(clang_path):
                    common.check_execute(['rm', clang_path])
                else:
                    continue

            common.check_execute(['mv', clang_orig_path, clang_path])
        self.clang_paths = []

    def __del__(self):
        self.clear()