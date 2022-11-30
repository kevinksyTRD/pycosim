import os
import unittest
from random import random, choice

from pyOSPParser.logging_configuration import OspLoggingConfiguration
from pyOSPParser.scenario import OSPScenario, OSPEvent

from pycosim.osp_command_line import LoggingLevel
from pycosim.simulation import SimulationConfiguration

_module_path = os.path.dirname(os.path.abspath(__file__))
PATH_TO_FMU = os.path.join(_module_path, os.path.pardir, "test_data", "fmus_system", "chassis.fmu")
PATH_TO_FMU_DIR = os.path.dirname(PATH_TO_FMU)
PATH_TO_SYSTEM_STRUCTURE_FILE_WITH_PROXY = os.path.join(
    PATH_TO_FMU_DIR, 'OspSystemStructureFmuProxy.xml'
)
PATH_TO_LOG_CONFIG = os.path.join(PATH_TO_FMU_DIR, "LogConfig.xml")
with open(PATH_TO_SYSTEM_STRUCTURE_FILE_WITH_PROXY, "rt") as file:
    osp_system_structure_with_proxy_xml_str = file.read()


class TestRunSimulation(unittest.TestCase):

    def test_run_cosim_with_local_proxy_servers(self):
        simulation_end_time = 10 + random() * 90

        sim_config = SimulationConfiguration(
            system_structure=osp_system_structure_with_proxy_xml_str,
            path_to_fmu=PATH_TO_FMU_DIR
        )
        scenario = OSPScenario(
            name='test_scenario',
            end=0.5 * simulation_end_time
        )
        scenario.add_event(OSPEvent(
            time=0.5 * scenario.end,
            model=sim_config.components[0].name,
            variable=choice(sim_config.components[0].fmu.parameters).get('name'),
            action=OSPEvent.OVERRIDE,
            value=random() * 10
        ))
        sim_config.scenario = scenario
        logging_config = OspLoggingConfiguration(
            xml_source=PATH_TO_LOG_CONFIG
        )
        sim_config.logging_config = logging_config

        result = sim_config.run_simulation(
            duration=simulation_end_time,
            rel_path_to_sys_struct="system_structure",
            logging_level=LoggingLevel.info,
            for_old_cosim=True,
            time_out_s=60
        )
        print(result.log)
        self.assertEqual(
            len(result.error), 0, f"There are errors during simulation\n {result.error}"
        )
        self.assertGreater(len(result.result), 0, "There is no output from the simulation")


if __name__ == '__main__':
    unittest.main()
