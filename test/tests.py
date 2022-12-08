import glob
import os
import shutil
import unittest
from random import random, choice

from pyOSPParser.logging_configuration import OspLoggingConfiguration
from pyOSPParser.scenario import OSPScenario, OSPEvent

from pycosim.osp_command_line import LoggingLevel, PATH_TO_OLD_COSIM, PATH_TO_COSIM
from pycosim.simulation import SimulationConfiguration

_module_path = os.path.dirname(os.path.abspath(__file__))
PATH_TO_FMU = os.path.join(
    _module_path, os.path.pardir, "test_data", "fmus_system", "chassis.fmu"
)
PATH_TO_FMU_DIR = os.path.dirname(PATH_TO_FMU)
PATH_TO_SYSTEM_STRUCTURE_FILE_WITH_PROXY = os.path.join(
    PATH_TO_FMU_DIR, "OspSystemStructureFmuProxy.xml"
)
PATH_TO_LOG_CONFIG = os.path.join(PATH_TO_FMU_DIR, "LogConfig.xml")
with open(PATH_TO_SYSTEM_STRUCTURE_FILE_WITH_PROXY, "rt") as file:
    osp_system_structure_with_proxy_xml_str = file.read()


class TestRunSimulation(unittest.TestCase):

    def doCleanups(self) -> None:
        self.sim_config = None
        if self.keep_simulation_files:
            self.assertGreater(
                len(os.listdir(self.path_to_deploy)), 0, "The deployment folder is empty"
            )
            shutil.rmtree(self.path_to_deploy)
        else:
            if os.path.isdir(self.path_to_deploy):
               files = os.listdir(self.path_to_deploy)
               if len(files) > 0:
                   self.assertTrue(files[0].endswith(".zip"), "The file should be a zip file")
            else:
                self.assertTrue(
                    not os.path.isdir(self.path_to_deploy) or
                    len(os.listdir(self.path_to_deploy)) == 0,
                    "The deployment folder is not deleted"
                )

    def setUp(self) -> None:
        self.keep_simulation_files = False
        self.path_to_deploy = os.path.join(_module_path, os.path.pardir, "temp_deploy")
        if os.path.exists(self.path_to_deploy):
            shutil.rmtree(self.path_to_deploy)
        os.makedirs(self.path_to_deploy)
        self.simulation_end_time = 10 + random() * 90
        self.sim_config = SimulationConfiguration(
            system_structure=osp_system_structure_with_proxy_xml_str,
            path_to_fmu=PATH_TO_FMU_DIR,
        )
        scenario = OSPScenario(name="test_scenario", end=0.5 * self.simulation_end_time)
        scenario.add_event(
            OSPEvent(
                time=0.5 * scenario.end,
                model=self.sim_config.components[0].name,
                variable=choice(self.sim_config.components[0].fmu.parameters).get(
                    "name"
                ),
                action=OSPEvent.OVERRIDE,
                value=random() * 10,
            )
        )
        self.sim_config.scenario = scenario
        logging_config = OspLoggingConfiguration(xml_source=PATH_TO_LOG_CONFIG)
        self.sim_config.logging_config = logging_config


    def test_run_cosim_with_local_proxy_servers(self):
        """Run the simulation with local proxy servers"""
        result = self.sim_config.run_simulation(
            duration=self.simulation_end_time,
            rel_path_to_sys_struct="system_structure",
            logging_level=LoggingLevel.info,
            for_old_cosim=True,
            time_out_s=60,
        )
        print(result.log)
        self.assertEqual(
            len(result.error), 0, f"There are errors during simulation\n {result.error}"
        )
        self.assertGreater(
            len(result.result), 0, "There is no output from the simulation"
        )

    def _check_package(self, path_deployed: str, path_to_bin: str):
        # check if the bin files are copied
        bin_files = [
            os.path.basename(file_path) for file_path in os.listdir(path_to_bin)
        ]
        for bin_file in bin_files:
            self.assertTrue(
                os.path.exists(os.path.join(path_deployed, "bin", bin_file)),
                f"The file {bin_file} is not copied to the deployment folder",
            )

        # Check batch files
        paths_for_batch_file = glob.glob(os.path.join(path_deployed, "*.bat"))
        self.assertEqual(
            len(paths_for_batch_file), 2, "There should be two batch files"
        )
        for batch_file_path in paths_for_batch_file:
            print(f"{os.path.basename(batch_file_path)} contains:")
            with open(batch_file_path, "rt") as batch_file:
                print(batch_file.read())

        self.assertTrue(
            os.path.exists(os.path.join(path_deployed, "OspSystemStructure.xml"))
        )

    def test_deploying_the_package_for_old_cosim(self):
        """Deploy the package to a local pc"""
        self.sim_config.deploy_simulation_package(
            path_to_deploy=self.path_to_deploy,
            for_old_cosim=True,
            duration=150,
            keep_simulation_files=self.keep_simulation_files
        )
        self._check_package(
            path_deployed=self.path_to_deploy, path_to_bin=os.path.dirname(PATH_TO_OLD_COSIM)
        )

    def test_deploying_the_package_for_new_cosim(self):
        """Deploy the package for new cosim to a local pc"""
        self.sim_config.deploy_simulation_package(
            path_to_deploy=self.path_to_deploy,
            for_old_cosim=False,
            duration=150,
            keep_simulation_files=self.keep_simulation_files
        )
        self._check_package(
            path_deployed=self.path_to_deploy, path_to_bin=os.path.dirname(PATH_TO_COSIM)
        )

    def test_export_simulation_package_to_zip(self):
        """Deploy the package as a zip file"""
        name = "test_export_simulation_package"
        self.sim_config.export_simulation_package_to_zip(
            path_to_dir=self.path_to_deploy,
            name="test_export_simulation_package",
            for_old_cosim=True,
            duration=150,
        )
        self.assertTrue(
            os.path.exists(os.path.join(self.path_to_deploy, f"{name}.zip")),
            "The zip file is not created",
        )

    def test_export_simulation_package_and_keep_files(self):
        """Deploy the package for new cosim to a local pc"""
        self.keep_simulation_files = True
        self.sim_config.deploy_simulation_package(
            path_to_deploy=self.path_to_deploy,
            for_old_cosim=False,
            duration=150,
            keep_simulation_files=True
        )

    def test_deploy_files_without_fmus(self):
        """Deploy the package without FMUs"""
        rel_path_to_sys_struct = "system_structure"
        self.sim_config.deploy_files_for_simulation(
            path_to_deploy=self.path_to_deploy,
            rel_path_to_system_structure=rel_path_to_sys_struct,
            skip_fmu_copy=True,
        )
        for file_name in os.listdir(self.path_to_deploy):
            self.assertNotIn(".fmu", file_name, "There should be no FMU files")
            self.assertNotIn(".xml", file_name, "There should be no XML files")
        files_deployed = os.listdir(os.path.join(self.path_to_deploy, rel_path_to_sys_struct))
        self.assertIn("LogConfig.xml", files_deployed, "The log config file is not copied")
        self.assertIn(
            "OspSystemStructure.xml", files_deployed, "The system structure file is not copied"
        )
        self.assertIn("scenarios", files_deployed, "The scenario file is not copied")

if __name__ == "__main__":
    unittest.main()
