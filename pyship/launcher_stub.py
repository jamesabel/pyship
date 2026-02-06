import subprocess
import tempfile
from pathlib import Path
from typing import Union

from typeguard import typechecked
from balsa import get_logger

from pyship import __application_name__

log = get_logger(__application_name__)

# C# source template for the launcher stub.
# Placeholders: {app_name}
# The stub finds the latest CLIP directory and runs the standalone Python launcher script.
CS_LAUNCHER_TEMPLATE = r"""
using System;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Reflection;

class Program
{{
    static int Main(string[] args)
    {{
        string appName = "{app_name}";
        string exePath = Assembly.GetEntryAssembly().Location;
        string launcherDir = Path.GetDirectoryName(exePath);
        string appDir = Directory.GetParent(launcherDir).FullName;

        // Find CLIP directories matching appName_version pattern
        string searchPattern = appName + "_*";
        string[] clipDirs;
        try
        {{
            clipDirs = Directory.GetDirectories(appDir, searchPattern);
        }}
        catch (Exception)
        {{
            clipDirs = new string[0];
        }}

        // Filter to directories that contain Scripts\python.exe
        var validClips = clipDirs
            .Where(d => File.Exists(Path.Combine(d, "Scripts", "python.exe")))
            .ToArray();

        if (validClips.Length == 0)
        {{
            string msg = "No Python environment found for " + appName + " in " + appDir;
            {error_handler}
            return 1;
        }}

        // Sort by version (directory name after appName_) and pick the latest
        Array.Sort(validClips, (a, b) =>
        {{
            string verA = Path.GetFileName(a).Substring(appName.Length + 1);
            string verB = Path.GetFileName(b).Substring(appName.Length + 1);
            return CompareVersions(verA, verB);
        }});

        string latestClip = validClips[validClips.Length - 1];
        string pythonExe = Path.Combine(latestClip, "Scripts", "python.exe");
        string launcherScript = Path.Combine(launcherDir, appName + "_launcher.py");

        if (!File.Exists(launcherScript))
        {{
            string msg = "Launcher script not found: " + launcherScript;
            {error_handler}
            return 1;
        }}

        // Build arguments: launcher script path + forwarded args
        string arguments = "\"" + launcherScript + "\" --app-dir \"" + appDir + "\"";
        foreach (string arg in args)
        {{
            arguments += " \"" + arg + "\"";
        }}

        ProcessStartInfo psi = new ProcessStartInfo();
        psi.FileName = pythonExe;
        psi.Arguments = arguments;
        psi.UseShellExecute = false;
        psi.WorkingDirectory = launcherDir;

        try
        {{
            Process process = Process.Start(psi);
            process.WaitForExit();
            return process.ExitCode;
        }}
        catch (Exception ex)
        {{
            string msg = "Failed to start: " + ex.Message;
            {error_handler}
            return 1;
        }}
    }}

    static int CompareVersions(string a, string b)
    {{
        string[] partsA = a.Split('.');
        string[] partsB = b.Split('.');
        int maxLen = Math.Max(partsA.Length, partsB.Length);
        for (int i = 0; i < maxLen; i++)
        {{
            int numA = 0, numB = 0;
            if (i < partsA.Length) int.TryParse(partsA[i], out numA);
            if (i < partsB.Length) int.TryParse(partsB[i], out numB);
            if (numA != numB) return numA.CompareTo(numB);
        }}
        return 0;
    }}
}}
"""

CLI_ERROR_HANDLER = "Console.Error.WriteLine(msg);"
GUI_ERROR_HANDLER = (
    'string logPath = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), appName, "log", appName + "_launcher.log");'
    ' msg += "\\n\\nLog file: " + logPath;'
    " System.Windows.Forms.MessageBox.Show(msg, appName, System.Windows.Forms.MessageBoxButtons.OK, System.Windows.Forms.MessageBoxIcon.Error);"
)


@typechecked
def _find_csc_exe() -> Union[Path, None]:
    """
    Locate the C# compiler (csc.exe) from .NET Framework.
    :return: path to csc.exe or None if not found
    """
    candidates = [
        Path(r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe"),
        Path(r"C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


@typechecked
def compile_launcher_stub(app_name: str, icon_path: Union[Path, None], is_gui: bool, output_path: Path) -> Path:
    """
    Compile the C# launcher stub into an .exe using csc.exe.
    :param app_name: target application name
    :param icon_path: path to .ico file (or None for no icon)
    :param is_gui: True for GUI app (winexe target), False for CLI (exe target)
    :param output_path: directory where the .exe will be written
    :return: path to the compiled .exe
    """
    csc_exe = _find_csc_exe()
    if csc_exe is None:
        raise FileNotFoundError("Could not find csc.exe (.NET Framework C# compiler). Ensure .NET Framework 4.x is installed.")

    error_handler = GUI_ERROR_HANDLER if is_gui else CLI_ERROR_HANDLER

    cs_source = CS_LAUNCHER_TEMPLATE.format(
        app_name=app_name,
        error_handler=error_handler,
    )

    output_path.mkdir(parents=True, exist_ok=True)
    exe_path = Path(output_path, f"{app_name}.exe")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".cs", delete=False, dir=str(output_path)) as cs_file:
        cs_file.write(cs_source)
        cs_file_path = cs_file.name

    try:
        target = "/target:winexe" if is_gui else "/target:exe"
        cmd = [
            str(csc_exe),
            target,
            "/optimize+",
            "/nologo",
            f"/out:{exe_path}",
            "/reference:System.Core.dll",  # required for LINQ
        ]

        if icon_path is not None and icon_path.exists():
            cmd.append(f"/win32icon:{icon_path}")

        if is_gui:
            cmd.append("/reference:System.Windows.Forms.dll")

        cmd.append(cs_file_path)

        log.info(f"compiling launcher stub: {cmd}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            log.error(f"csc.exe compilation failed:\nstdout: {result.stdout}\nstderr: {result.stderr}")
            raise RuntimeError(f"C# compilation failed: {result.stderr}")
        log.info(f"launcher stub compiled: {exe_path}")
    finally:
        try:
            Path(cs_file_path).unlink()
        except OSError:
            pass

    return exe_path
