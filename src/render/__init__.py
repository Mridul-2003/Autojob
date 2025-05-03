import os
import shutil
import subprocess
import tempfile

def render_latex(latex_command, latex_data):
    src_path = os.path.dirname(os.path.realpath(__file__)) + "/inputs"

    with tempfile.TemporaryDirectory() as tmpdirname:
        # Copy auxiliary files to temporary directory
        shutil.copytree(src_path, tmpdirname, dirs_exist_ok=True)

        # Write LaTeX data to a file
        with open(f"{tmpdirname}/resume.tex", "w") as f:
            f.write(latex_data)

        # Log the LaTeX content for troubleshooting
        print("Generated LaTeX content:")
        print(latex_data)

        # Prepare the environment
        latex_env = os.environ.copy()
        latex_env["PATH"] = "/Library/TeX/texbin:" + latex_env.get("PATH", "")

        # Ensure latex_command is a list
        if isinstance(latex_command, str):
            latex_command = latex_command.split()

        # Run LaTeX command
        try:
            latex_process = subprocess.Popen(
                latex_command,
                cwd=tmpdirname,
                env=latex_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = latex_process.communicate()

            if latex_process.returncode != 0:
                print("LaTeX compilation failed with the following error:")
                print(stderr.decode())  # Log LaTeX error output
                print(stdout.decode())  # Log LaTeX standard output
                return None  # Handle the error as needed

            # Read PDF data
            with open(f"{tmpdirname}/resume.pdf", "rb") as f:
                pdf_data = f.read()

            return pdf_data

        except Exception as e:
            print(f"Error during LaTeX rendering: {e}")
            return None
