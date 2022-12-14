import os
from typing import Union
from pathlib import Path
from textwrap import dedent
from datetime import datetime


class EXTRACT_trigger:
    m_template = dedent(
        """
        % Load Data
        data = load('{scanfile}');
        M = data.M;
        
        % Input Paramaters
        config = struct();
        {parameters_list_string}
        
        % Perform Extraction
        output = extractor(M, config);
        save('{output_fullpath}', 'output');
        """
    )

    def __init__(
        self,
        scanfile_fullpath: Union[str, Path],
        parameters: dict,
        output_dir: Union[str, Path],
    ) -> None:
        """A helper class to trigger EXTRACT analysis in element-calcium-imaging.

        Args:
            scanfile_fullpath (Union[str, Path]): Full path of the scan
            parameters (dict): EXTRACT input paramaters.
            output_dir (Union[str, Path]): Directory to store the outputs of EXTRACT analysis.
        """
        assert isinstance(parameters, dict)

        self.scanfile = Path(scanfile_fullpath)
        self.output_dir = Path(output_dir)
        self.parameters = parameters

    def write_matlab_run_script(self):
        """Compose a matlab script and save it with the name run_extract.m.

        The composed script is basically the formatted version of the m_template attribute."""

        self.output_fullpath = (
            self.output_dir / f"{self.scanfile.stem}_extract_output.mat"
        )

        m_file_content = self.m_template.format(
            **dict(
                parameters_list_string="\n".join(
                    [
                        f"config.{k} = '{v}';"
                        if isinstance(v, str)
                        else f"config.{k} = {str(v).lower()};"
                        if isinstance(v, bool)
                        else f"config.{k} = {v};"
                        for k, v in self.parameters.items()
                    ]
                ),
                scanfile=self.scanfile,
                output_fullpath=self.output_fullpath.as_posix(),
            )
        ).lstrip()

        self.m_file_fp = self.output_dir / "run_extract.m"

        with open(self.m_file_fp, "w") as f:
            f.write(m_file_content)

    def run(self):
        """Run the matlab run_extract.m script."""

        self.write_matlab_run_script()

        current_dir = Path.cwd()
        os.chdir(self.output_dir)

        run_status = {"processing_time": datetime.utcnow()}
        try:
            import matlab.engine

            eng = matlab.engine.start_matlab()
            eng.run_extract()
        except Exception as e:
            raise e
        finally:
            os.chdir(current_dir)

        run_status["execution_duration"] = (
            datetime.utcnow() - run_status["processing_time"]
        ).total_seconds()