#!/usr/bin/env python
# encoding: utf-8
"""
The main IPython application object

Authors:

* Brian Granger
* Fernando Perez

Notes
-----
"""

#-----------------------------------------------------------------------------
#  Copyright (C) 2008-2009  The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------

import logging
import os
import sys
import warnings

from IPython.core.application import Application, IPythonArgParseConfigLoader
from IPython.core import release
from IPython.core.iplib import InteractiveShell
from IPython.config.loader import (
    NoConfigDefault, 
    Config,
    ConfigError,
    PyFileConfigLoader
)

from IPython.utils.ipstruct import Struct
from IPython.utils.genutils import filefind, get_ipython_dir

#-----------------------------------------------------------------------------
# Utilities and helpers
#-----------------------------------------------------------------------------


ipython_desc = """
A Python shell with automatic history (input and output), dynamic object
introspection, easier configuration, command completion, access to the system
shell and more.
"""

def threaded_shell_warning():
    msg = """

The IPython threaded shells and their associated command line
arguments (pylab/wthread/gthread/qthread/q4thread) have been 
deprecated.  See the %gui magic for information on the new interface.
"""
    warnings.warn(msg, category=DeprecationWarning, stacklevel=1)


#-----------------------------------------------------------------------------
# Main classes and functions
#-----------------------------------------------------------------------------

cl_args = (
    (('-autocall',), dict(
        type=int, dest='InteractiveShell.autocall', default=NoConfigDefault,
        help='Set the autocall value (0,1,2).',
        metavar='InteractiveShell.autocall')
    ),
    (('-autoindent',), dict(
        action='store_true', dest='InteractiveShell.autoindent', default=NoConfigDefault,
        help='Turn on autoindenting.')
    ),
    (('-noautoindent',), dict(
        action='store_false', dest='InteractiveShell.autoindent', default=NoConfigDefault,
        help='Turn off autoindenting.')
    ),
    (('-automagic',), dict(
        action='store_true', dest='InteractiveShell.automagic', default=NoConfigDefault,
        help='Turn on the auto calling of magic commands.')
    ),
    (('-noautomagic',), dict(
        action='store_false', dest='InteractiveShell.automagic', default=NoConfigDefault,
        help='Turn off the auto calling of magic commands.')
    ),
    (('-autoedit_syntax',), dict(
        action='store_true', dest='InteractiveShell.autoedit_syntax', default=NoConfigDefault,
        help='Turn on auto editing of files with syntax errors.')
    ),
    (('-noautoedit_syntax',), dict(
        action='store_false', dest='InteractiveShell.autoedit_syntax', default=NoConfigDefault,
        help='Turn off auto editing of files with syntax errors.')
    ),
    (('-banner',), dict(
        action='store_true', dest='Global.display_banner', default=NoConfigDefault,
        help='Display a banner upon starting IPython.')
    ),
    (('-nobanner',), dict(
        action='store_false', dest='Global.display_banner', default=NoConfigDefault,
        help="Don't display a banner upon starting IPython.")
    ),
    (('-c',), dict(
        type=str, dest='InteractiveShell.c', default=NoConfigDefault,
        help="Execute the given command string.",
        metavar='InteractiveShell.c')
    ),
    (('-cache_size',), dict(
        type=int, dest='InteractiveShell.cache_size', default=NoConfigDefault,
        help="Set the size of the output cache.",
        metavar='InteractiveShell.cache_size')
    ),
    (('-classic',), dict(
        action='store_true', dest='Global.classic', default=NoConfigDefault,
        help="Gives IPython a similar feel to the classic Python prompt.")
    ),
    (('-colors',), dict(
        type=str, dest='InteractiveShell.colors', default=NoConfigDefault,
        help="Set the color scheme (NoColor, Linux, and LightBG).",
        metavar='InteractiveShell.colors')
    ),
    (('-color_info',), dict(
        action='store_true', dest='InteractiveShell.color_info', default=NoConfigDefault,
        help="Enable using colors for info related things.")
    ),
    (('-nocolor_info',), dict(
        action='store_false', dest='InteractiveShell.color_info', default=NoConfigDefault,
        help="Disable using colors for info related things.")
    ),
    (('-confirm_exit',), dict(
        action='store_true', dest='InteractiveShell.confirm_exit', default=NoConfigDefault,
        help="Prompt the user when existing.")
    ),
    (('-noconfirm_exit',), dict(
        action='store_false', dest='InteractiveShell.confirm_exit', default=NoConfigDefault,
        help="Don't prompt the user when existing.")
    ),
    (('-deep_reload',), dict(
        action='store_true', dest='InteractiveShell.deep_reload', default=NoConfigDefault,
        help="Enable deep (recursive) reloading by default.")
    ),
    (('-nodeep_reload',), dict(
        action='store_false', dest='InteractiveShell.deep_reload', default=NoConfigDefault,
        help="Disable deep (recursive) reloading by default.")
    ),
    (('-editor',), dict(
        type=str, dest='InteractiveShell.editor', default=NoConfigDefault,
        help="Set the editor used by IPython (default to $EDITOR/vi/notepad).",
        metavar='InteractiveShell.editor')
    ),
    (('-log','-l'), dict(
        action='store_true', dest='InteractiveShell.logstart', default=NoConfigDefault,
        help="Start logging to the default file (./ipython_log.py).")
    ),
    (('-logfile','-lf'), dict(
        type=str, dest='InteractiveShell.logfile', default=NoConfigDefault,
        help="Specify the name of your logfile.",
        metavar='InteractiveShell.logfile')
    ),
    (('-logplay','-lp'), dict(
        type=str, dest='InteractiveShell.logplay', default=NoConfigDefault,
        help="Re-play a log file and then append to it.",
        metavar='InteractiveShell.logplay')
    ),
    (('-pdb',), dict(
        action='store_true', dest='InteractiveShell.pdb', default=NoConfigDefault,
        help="Enable auto calling the pdb debugger after every exception.")
    ),
    (('-nopdb',), dict(
        action='store_false', dest='InteractiveShell.pdb', default=NoConfigDefault,
        help="Disable auto calling the pdb debugger after every exception.")
    ),
    (('-pprint',), dict(
        action='store_true', dest='InteractiveShell.pprint', default=NoConfigDefault,
        help="Enable auto pretty printing of results.")
    ),
    (('-nopprint',), dict(
        action='store_false', dest='InteractiveShell.pprint', default=NoConfigDefault,
        help="Disable auto auto pretty printing of results.")
    ),
    (('-prompt_in1','-pi1'), dict(
        type=str, dest='InteractiveShell.prompt_in1', default=NoConfigDefault,
        help="Set the main input prompt ('In [\#]: ')",
        metavar='InteractiveShell.prompt_in1')
    ),
    (('-prompt_in2','-pi2'), dict(
        type=str, dest='InteractiveShell.prompt_in2', default=NoConfigDefault,
        help="Set the secondary input prompt (' .\D.: ')",
        metavar='InteractiveShell.prompt_in2')
    ),
    (('-prompt_out','-po'), dict(
        type=str, dest='InteractiveShell.prompt_out', default=NoConfigDefault,
        help="Set the output prompt ('Out[\#]:')",
        metavar='InteractiveShell.prompt_out')
    ),
    (('-quick',), dict(
        action='store_true', dest='Global.quick', default=NoConfigDefault,
        help="Enable quick startup with no config files.")
    ),
    (('-readline',), dict(
        action='store_true', dest='InteractiveShell.readline_use', default=NoConfigDefault,
        help="Enable readline for command line usage.")
    ),
    (('-noreadline',), dict(
        action='store_false', dest='InteractiveShell.readline_use', default=NoConfigDefault,
        help="Disable readline for command line usage.")
    ),
    (('-screen_length','-sl'), dict(
        type=int, dest='InteractiveShell.screen_length', default=NoConfigDefault,
        help='Number of lines on screen, used to control printing of long strings.',
        metavar='InteractiveShell.screen_length')
    ),
    (('-separate_in','-si'), dict(
        type=str, dest='InteractiveShell.separate_in', default=NoConfigDefault,
        help="Separator before input prompts.  Default '\n'.",
        metavar='InteractiveShell.separate_in')
    ),
    (('-separate_out','-so'), dict(
        type=str, dest='InteractiveShell.separate_out', default=NoConfigDefault,
        help="Separator before output prompts.  Default 0 (nothing).",
        metavar='InteractiveShell.separate_out')
    ),
    (('-separate_out2','-so2'), dict(
        type=str, dest='InteractiveShell.separate_out2', default=NoConfigDefault,
        help="Separator after output prompts.  Default 0 (nonight).",
        metavar='InteractiveShell.separate_out2')
    ),
    (('-nosep',), dict(
        action='store_true', dest='Global.nosep', default=NoConfigDefault,
        help="Eliminate all spacing between prompts.")
    ),
    (('-term_title',), dict(
        action='store_true', dest='InteractiveShell.term_title', default=NoConfigDefault,
        help="Enable auto setting the terminal title.")
    ),
    (('-noterm_title',), dict(
        action='store_false', dest='InteractiveShell.term_title', default=NoConfigDefault,
        help="Disable auto setting the terminal title.")
    ),
    (('-xmode',), dict(
        type=str, dest='InteractiveShell.xmode', default=NoConfigDefault,
        help="Exception mode ('Plain','Context','Verbose')",
        metavar='InteractiveShell.xmode')
    ),
    (('-ext',), dict(
        type=str, dest='Global.extra_extension', default=NoConfigDefault,
        help="The dotted module name of an IPython extension to load.",
        metavar='Global.extra_extension')
    ),
    # These are only here to get the proper deprecation warnings
    (('-pylab','-wthread','-qthread','-q4thread','-gthread'), dict(
        action='store_true', dest='Global.threaded_shell', default=NoConfigDefault,
        help="These command line flags are deprecated, see the 'gui' magic.")
    ),
)


class IPythonAppCLConfigLoader(IPythonArgParseConfigLoader):

    arguments = cl_args


_default_config_file_name = 'ipython_config.py'

class IPythonApp(Application):
    name = 'ipython'
    config_file_name = _default_config_file_name

    def create_default_config(self):
        super(IPythonApp, self).create_default_config()
        self.default_config.Global.display_banner=True
        # Let the parent class set the default, but each time log_level
        # changes from config, we need to update self.log_level as that is
        # what updates the actual log level in self.log.
        self.default_config.Global.log_level = self.log_level

    def create_command_line_config(self):
        """Create and return a command line config loader."""
        return IPythonAppCLConfigLoader(
            description=ipython_desc,
            version=release.version)

    def post_load_command_line_config(self):
        """Do actions after loading cl config."""
        clc = self.command_line_config

        # Display the deprecation warnings about threaded shells
        if hasattr(clc.Global, 'threaded_shell'):
            threaded_shell_warning()
            del clc.Global['threaded_shell']

    def load_file_config(self):
        if hasattr(self.command_line_config.Global, 'quick'):
            if self.command_line_config.Global.quick:
                self.file_config = Config()
                return
        super(IPythonApp, self).load_file_config()

    def post_load_file_config(self):
        if hasattr(self.command_line_config.Global, 'extra_extension'):
            if not hasattr(self.file_config.Global, 'extensions'):
                self.file_config.Global.extensions = []
            self.file_config.Global.extensions.append(
                self.command_line_config.Global.extra_extension)
            del self.command_line_config.Global.extra_extension

    def pre_construct(self):
        config = self.master_config

        if hasattr(config.Global, 'classic'):
            if config.Global.classic:
                config.InteractiveShell.cache_size = 0
                config.InteractiveShell.pprint = 0
                config.InteractiveShell.prompt_in1 = '>>> '
                config.InteractiveShell.prompt_in2 = '... '
                config.InteractiveShell.prompt_out = ''
                config.InteractiveShell.separate_in = \
                    config.InteractiveShell.separate_out = \
                    config.InteractiveShell.separate_out2 = ''
                config.InteractiveShell.colors = 'NoColor'
                config.InteractiveShell.xmode = 'Plain'

        # All this should be moved to traitlet handlers in InteractiveShell
        # But, currently InteractiveShell doesn't have support for changing
        # these values at runtime.  Once we support that, this should
        # be moved there!!!
        if hasattr(config.Global, 'nosep'):
            if config.Global.nosep:
                config.InteractiveShell.separate_in = \
                config.InteractiveShell.separate_out = \
                config.InteractiveShell.separate_out2 = '0'

    def construct(self):
        # I am a little hesitant to put these into InteractiveShell itself.
        # But that might be the place for them
        sys.path.insert(0, '')

        # Create an InteractiveShell instance
        self.shell = InteractiveShell(
            parent=None,
            config=self.master_config
        )

    def post_construct(self):
        """Do actions after construct, but before starting the app."""
        # shell.display_banner should always be False for the terminal 
        # based app, because we call shell.show_banner() by hand below
        # so the banner shows *before* all extension loading stuff.
        self.shell.display_banner = False

        if self.master_config.Global.display_banner:
            self.shell.show_banner()

        # Make sure there is a space below the banner.
        if self.log_level <= logging.INFO: print

        self._load_extensions()
        self._run_exec_lines()
        self._run_exec_files()

    def _load_extensions(self):
        """Load all IPython extensions in Global.extensions.

        This uses the :meth:`InteractiveShell.load_extensions` to load all
        the extensions listed in ``self.master_config.Global.extensions``.
        """
        try:
            if hasattr(self.master_config.Global, 'extensions'):
                self.log.debug("Loading IPython extensions...")
                extensions = self.master_config.Global.extensions
                for ext in extensions:
                    try:
                        self.log.info("Loading IPython extension: %s" % ext)                        
                        self.shell.load_extension(ext)
                    except:
                        self.log.warn("Error in loading extension: %s" % ext)
                        self.shell.showtraceback()
        except:
            self.log.warn("Unknown error in loading extensions:")
            self.shell.showtraceback()

    def _run_exec_lines(self):
        """Run lines of code in Global.exec_lines in the user's namespace."""
        try:
            if hasattr(self.master_config.Global, 'exec_lines'):
                self.log.debug("Running code from Global.exec_lines...")
                exec_lines = self.master_config.Global.exec_lines
                for line in exec_lines:
                    try:
                        self.log.info("Running code in user namespace: %s" % line)
                        self.shell.runlines(line)
                    except:
                        self.log.warn("Error in executing line in user namespace: %s" % line)
                        self.shell.showtraceback()
        except:
            self.log.warn("Unknown error in handling Global.exec_lines:")
            self.shell.showtraceback()

    def _run_exec_files(self):
        try:
            if hasattr(self.master_config.Global, 'exec_files'):
                self.log.debug("Running files in Global.exec_files...")
                exec_files = self.master_config.Global.exec_files
                for fname in exec_files:
                    full_filename = filefind(fname, ['.', self.ipythondir])
                    if os.path.isfile(full_filename):
                        if full_filename.endswith('.py'):
                            self.log.info("Running file in user namespace: %s" % full_filename)
                            self.shell.safe_execfile(full_filename, self.shell.user_ns)
                        elif full_filename.endswith('.ipy'):
                            self.log.info("Running file in user namespace: %s" % full_filename)
                            self.shell.safe_execfile_ipy(full_filename)
                        else:
                            self.log.warn("File does not have a .py or .ipy extension: <%s>" % full_filename)
        except:
            self.log.warn("Unknown error in handling Global.exec_files:")
            self.shell.showtraceback()

    def start_app(self):
        self.log.debug("Starting IPython's mainloop...")
        self.shell.mainloop()


def load_default_config(ipythondir=None):
    """Load the default config file from the default ipythondir.

    This is useful for embedded shells.
    """
    if ipythondir is None:
        ipythondir = get_ipython_dir()
    cl = PyFileConfigLoader(_default_config_file_name, ipythondir)
    config = cl.load_config()
    return config


if __name__ == '__main__':
    app = IPythonApp()
    app.start()