from eddie_helper.make_scripts import run_python_script, run_stage_script

from argparse import ArgumentParser
from pathlib import Path

def main():

    parser = ArgumentParser()

    parser.add_argument('mouse')
    parser.add_argument('day')
    parser.add_argument('session')
    parser.add_argument('bodypart')
    parser.add_argument('--data_folder', default="")
    parser.add_argument('--deriv_folder', default="")

    mouse = int(parser.parse_args().mouse)
    day = int(parser.parse_args().day)
    session = parser.parse_args().session
    bodypart = parser.parse_args().bodypart

    data_folder = parser.parse_args().data_folder
    if len(data_folder) == 0:
        data_folder = "/exports/eddie/scratch/chalcrow/wolf/data"
    data_folder = Path(data_folder)

    deriv_folder = parser.parse_args().deriv_folder
    if len(deriv_folder) == 0:
        deriv_folder = "/exports/eddie/scratch/chalcrow/wolf/derivatives"
    deriv_folder = Path(deriv_folder)

    run_python_name = f"M{mouse}D{day}{session[:2]}{bodypart}"
    stageout_job_name = f"M{mouse}D{day}{session[:2]}out" 

    eddie_active_projects = Path("/exports/cmvm/datastore/sbms/groups/CDBS_SIDB_storage/NolanLab/ActiveProjects/")
    stageout_dict = {deriv_folder / f"M{mouse:02d}/D{day:02d}/{session}/dlc_output_{bodypart}": eddie_active_projects / "Wolf/MMNAV/derivatives" / f"M{mouse:02d}/D{day:02d}/{session}/"}

    uv_directory = "/exports/eddie/scratch/chalcrow/wolf/code/nolanlab-dlc/"
    python_arg = f"pose_estimation.py {mouse} {day} {session} {bodypart} --data_folder {data_folder} --deriv_folder {deriv_folder}"

    run_python_script(uv_directory, python_arg, cores=8, email="chalcrow@ed.ac.uk", staging=False, job_name=run_python_name)
    run_stage_script(stageout_dict, job_name=stageout_job_name, hold_jid=run_python_name)

if __name__ == "__main__":
    main()