# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

"""
This file is mean to be called with a path to an example directory as
its argument.  We import the application entry point for the example
and add instrument them with a Playwright test that makes sure
there are no console errors or uncaught errors prior to a sentinel
string being printed.

e.g. python example_check.py ./app
"""
import importlib.util
import os
import shutil
import sys
from pathlib import Path

from jupyterlab.browser_check import run_async_process, run_test
from jupyterlab.labapp import get_app_dir

here = Path(__file__).parent.resolve()
TEST_FILE = here / "example.spec.ts"


def main():
    # Load the main file and grab the example class so we can subclass
    example_dir = Path(sys.argv.pop())
    mod_path = (example_dir / "main.py").resolve()
    spec = importlib.util.spec_from_file_location("example", mod_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    sys.modules[__name__] = mod

    class App(mod.ExampleApp):
        """An app that launches an example and waits for it to start up, checking for
        JS console errors, JS errors, and Python logged errors.
        """

        name = __name__
        open_browser = False

        serverapp_config = {
            "base_url": "/foo/",
            "root_dir": str(example_dir.resolve()),
            "preferred_dir": str(example_dir.resolve()),
        }
        ip = "127.0.0.1"

        def initialize_settings(self):
            run_test(self.serverapp, run_browser)
            super().initialize_settings()

        def _jupyter_server_extension_points():
            return [{"module": __name__, "app": App}]

        mod._jupyter_server_extension_points = _jupyter_server_extension_points

    App.__name__ = example_dir.name.capitalize() + "Test"
    App.launch_instance()


async def run_browser(url):
    """Run the browser test and return an exit code."""
    # Run the browser test and return an exit code.
    target = Path(get_app_dir()) / "example_test"
    if not (target / "node_modules").exists():
        if not target.exists():
            target.mkdir(parents=True, exist_ok=True)
        await run_async_process(["npm", "init", "-y"], cwd=str(target))
        await run_async_process(["npm", "install", "-D", "@playwright/test@^1"], cwd=str(target))
        await run_async_process(["npx", "playwright", "install", "chromium"], cwd=str(target))
    test_target = target / TEST_FILE.name

    shutil.copy(
        str(TEST_FILE),
        str(test_target),
    )

    current_env = os.environ.copy()
    current_env["BASE_URL"] = url
    await run_async_process(["npx", "playwright", "test"], env=current_env, cwd=str(target))


if __name__ == "__main__":
    main()
