# webview_host.py
# Developer: Marcus Daley
# Date: 2026-04-29
# Purpose: Encapsulate every WebView2 detail so the rest of the dashboard
#          stays free of pythonnet boilerplate. Detects whether the
#          Microsoft WebView2 Runtime is present, instantiates the WPF
#          control, navigates it to the dashboard URL, and exposes a
#          clean fallback that renders an HTML "please install the
#          runtime" page when the runtime is missing. Keeping all of
#          this behind a single class means the agentic_dashboard
#          module can compose the launcher in declarative form.

from __future__ import annotations

import logging
from typing import Any, Optional

from AgenticOS.dashboard import config as dashboard_config


_logger = logging.getLogger("AgenticOS.dashboard.webview_host")


# ---------------------------------------------------------------------------
# Static HTML fallback
#
# Served via NavigateToString when the WebView2 control loads but cannot
# reach the FastAPI server. Kept as a module-level constant rather than
# an external file so a missing /assets folder cannot break the fallback
# path itself.
# ---------------------------------------------------------------------------

_FALLBACK_HTML_TEMPLATE = """\
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{title}</title>
    <style>
      :root {{
        color-scheme: dark;
        --gold: #C9A94E;
        --navy: #1B2838;
        --parchment: #F5E6C8;
        --dim: #8899AA;
      }}
      html, body {{
        margin: 0;
        height: 100%;
        background: var(--navy);
        color: var(--parchment);
        font-family: "Segoe UI", system-ui, sans-serif;
      }}
      .stage {{
        max-width: 640px;
        margin: 10vh auto;
        padding: 32px;
        border: 1px solid var(--gold);
        border-radius: 8px;
        background: rgba(15, 26, 36, 0.85);
      }}
      h1 {{ color: var(--gold); margin-top: 0; }}
      a {{ color: var(--gold); }}
      code {{ color: var(--dim); }}
    </style>
  </head>
  <body>
    <div class="stage">
      <h1>{heading}</h1>
      <p>{body}</p>
      <p>
        <a href="{download_url}" target="_blank" rel="noopener">
          Open the WebView2 download page
        </a>
      </p>
      <p><code>{detail}</code></p>
    </div>
  </body>
</html>
"""


class WebView2NotInstalledError(RuntimeError):
    """Raised when the WebView2 runtime is not present on the host."""


class WebViewHost:
    """Builder for the WebView2 WPF control used in the dashboard.

    Designed as a one-shot helper: construct, call create_control,
    insert into the XAML host, then call navigate_to_dashboard. The
    object holds a reference to the underlying control so the caller
    can wire additional events (e.g. NavigationStarting) without
    digging the control out of the XAML tree.
    """

    def __init__(self, dashboard_url: str, fallback_html: str) -> None:
        # URL the control should navigate to when create_control succeeds.
        self._dashboard_url = dashboard_url
        # Pre-rendered HTML used by show_fallback_message; cached so the
        # template substitution only happens once per launcher run.
        self._fallback_html = fallback_html
        # Populated after create_control(); None means we are in fallback mode.
        self._control: Optional[Any] = None

    # ------------------------------------------------------------------
    # Construction-time discovery
    # ------------------------------------------------------------------

    @staticmethod
    def runtime_installed() -> bool:
        """Return True iff the Microsoft.Web.WebView2 assemblies load.

        Importing pythonnet's clr inside a try/except is the only
        portable way to probe for the runtime, since the runtime ships
        as a separate Microsoft installer and its absence presents as a
        FileNotFoundException from the .NET loader.
        """
        try:
            import clr  # type: ignore[import-not-found]

            # AddReference returns silently on success and raises on
            # failure; we only need the side effect.
            clr.AddReference("Microsoft.Web.WebView2.Wpf")
            clr.AddReference("Microsoft.Web.WebView2.Core")
            return True
        except Exception as exc:  # noqa: BLE001 - pythonnet uses a wide range
            _logger.warning("WebView2 runtime probe failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Control instantiation
    # ------------------------------------------------------------------

    def create_control(self) -> Any:
        """Build the WebView2 instance, raising if the runtime is absent.

        Returns the WPF control so the caller can drop it into a XAML
        Grid via Children.Add. The control is also stashed on this
        host for later operations (devtools toggle, navigation calls).
        """
        if not self.runtime_installed():
            # Surface this as a typed exception so callers can branch
            # cleanly rather than parsing exception messages.
            raise WebView2NotInstalledError(
                "Microsoft WebView2 Runtime is not installed"
            )

        # Imports happen inside the method because pythonnet only
        # registers the .NET namespaces after AddReference, which
        # runtime_installed() performed. Doing them at module import
        # time would crash on machines without the runtime.
        from Microsoft.Web.WebView2.Wpf import WebView2  # type: ignore[import-not-found]

        self._control = WebView2()
        # Configure devtools according to the debug flag from config so
        # production users never accidentally see the F12 menu.
        if dashboard_config.WEBVIEW2_DEVTOOLS_ENABLED:
            # CoreWebView2 is initialised lazily by the framework; hook
            # the readiness event so we can flip the dev-tools setting
            # the moment the underlying CoreWebView2 instance exists.
            self._control.CoreWebView2InitializationCompleted += (
                self._on_core_webview2_ready
            )
        return self._control

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def navigate_to_dashboard(self) -> None:
        """Point the WebView2 control at the React frontend URL.

        Uses the .NET System.Uri type rather than a raw string so the
        WebView2 control validates the URL during the property setter.
        """
        if self._control is None:
            raise RuntimeError("create_control must be called before navigation")

        from System import Uri  # type: ignore[import-not-found]

        self._control.Source = Uri(self._dashboard_url)
        _logger.info("WebView2 navigated to %s", self._dashboard_url)

    def show_fallback_message(self) -> None:
        """Render the in-process HTML page used when the runtime is missing.

        The control will not exist in this code path, so the dashboard
        is expected to render the fallback HTML through some other
        mechanism (e.g. a WPF FlowDocument) using ``self.fallback_html``.
        Exposed as a method on the host so callers always interact
        with one object, regardless of which branch they are in.
        """
        # The fallback path is implemented by the dashboard itself,
        # not by WebView2 (which we cannot use here). This method is
        # therefore a no-op in this module; documenting the fact keeps
        # call sites readable.
        _logger.info("Using static fallback HTML; WebView2 runtime missing")

    # ------------------------------------------------------------------
    # Public read accessors
    # ------------------------------------------------------------------

    @property
    def control(self) -> Optional[Any]:
        """Return the underlying WebView2 control or None in fallback mode."""
        return self._control

    @property
    def fallback_html(self) -> str:
        """Return the rendered fallback HTML for callers that need it."""
        return self._fallback_html

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_core_webview2_ready(self, _sender: Any, args: Any) -> None:
        """Enable devtools the moment the CoreWebView2 finishes initialising.

        Setting AreDevToolsEnabled before initialisation has no effect,
        which is why this is wired up via the readiness event rather
        than configured eagerly in create_control.
        """
        # IsSuccess is the documented way to check whether the control
        # actually came up; without it we would hide a real failure.
        try:
            success = bool(args.IsSuccess)
        except AttributeError:
            success = True

        if not success:
            _logger.warning("CoreWebView2 init reported failure; skipping devtools")
            return

        try:
            # The Settings property is exposed on CoreWebView2 once init
            # completes; mutating it here is safe.
            self._control.CoreWebView2.Settings.AreDevToolsEnabled = True
        except Exception as exc:  # noqa: BLE001
            _logger.warning("Could not enable WebView2 devtools: %s", exc)


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def render_fallback_html(detail: str = "") -> str:
    """Build the fallback HTML page from the template and the live URL.

    Centralised so the dashboard, the tests, and any future feature
    that needs the same UX share a single rendering path.
    """
    return _FALLBACK_HTML_TEMPLATE.format(
        title=dashboard_config.APP_DISPLAY_NAME,
        heading="WebView2 Runtime not detected",
        body=(
            "The AgenticOS Command Center hosts the React UI inside Microsoft "
            "WebView2. Install the runtime from Microsoft and relaunch the "
            "dashboard."
        ),
        download_url=dashboard_config.WEBVIEW2_DOWNLOAD_URL,
        detail=detail or "Probe failed: Microsoft.Web.WebView2.Wpf could not load.",
    )


def build_default_host() -> WebViewHost:
    """Construct a WebViewHost using the project-wide config defaults."""
    return WebViewHost(
        dashboard_url=dashboard_config.build_dashboard_url(),
        fallback_html=render_fallback_html(),
    )
