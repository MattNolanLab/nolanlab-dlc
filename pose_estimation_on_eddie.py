from eddie_helper.make_scripts import run_python_script, run_stage_script

import pandas as pd
from argparse import ArgumentParser
from pathlib import Path

def filepath_from_mouse_day_sessions(mouse, day, sessions, path_to_all_filepaths):
    
    all_filepaths = pd.read_csv(path_to_all_filepaths)
    sessions_filepaths = []
    
    for session in sessions:
        session_column = all_filepaths.query(f'mouse == {mouse} & day == {day} & session == "{session}"')
        filepath = session_column['filepath'].values[0]
        sessions_filepaths.append(filepath)

    return sessions_filepaths

def main():

    parser = ArgumentParser()

    parser.add_argument('mouse')
    parser.add_argument('day')
    parser.add_argument('session')
    parser.add_argument('bodypart')
    parser.add_argument('--data_folder', default="")
    parser.add_argument('--deriv_folder', default="")

    mouse = int(parser.parse_args().mouse)
    mouse_string = f"{mouse:02d}"
    
    day = int(parser.parse_args().day)
    day_string = f"{day:02d}"

    session = parser.parse_args().session
    bodypart = parser.parse_args().bodypart

    data_folder = parser.parse_args().data_folder
    if len(data_folder) == 0:
        data_folder = "/exports/eddie/scratch/chalcrow/data"
    data_folder = Path(data_folder)

    deriv_folder = parser.parse_args().deriv_folder
    if len(deriv_folder) == 0:
        deriv_folder = "/exports/eddie/scratch/chalcrow/derivatives"
    deriv_folder = Path(deriv_folder)
    
    recording_paths = filepath_from_mouse_day_sessions(mouse, day, sessions=[session], path_to_all_filepaths='../nolanlab-ephys/scripts/wolf/wolf_filepaths.csv')

    active_projects_path = Path("/exports/cmvm/datastore/sbms/groups/INCR-NolanLab/ActiveProjects/")
    
    stagein_dict = {}
    for recording_path in recording_paths:
        recording_folder_name = Path(recording_path).name
        if "OF" in recording_path:
            session_type_folder = data_folder / 'OF'
            stagein_dict[f"{active_projects_path / recording_path}"] = session_type_folder / recording_folder_name / f'M{mouse_string}_D{day_string}_*_{session}.avi'
        else:
            session_type_folder = data_folder / 'VR'
            stagein_dict[f"{active_projects_path / recording_path}"] = session_type_folder / recording_folder_name / f'M{mouse_string}_D{day_string}_{session}_side_capture.avi'
        session_type_folder.mkdir(exist_ok=True)
        (session_type_folder / recording_folder_name).mkdir(exist_ok=True)

    stagein_job_name = f"M{mouse}D{day}{session[:2]}in" 
    run_python_name = f"M{mouse}D{day}{session[:2]}{bodypart}"
    stageout_job_name = f"M{mouse}D{day}{session[:2]}out" 

    eddie_active_projects = Path("/exports/cmvm/datastore/sbms/groups/CDBS_SIDB_storage/NolanLab/ActiveProjects/")
    stageout_dict = {deriv_folder / f"M{mouse:02d}/D{day:02d}/{session}/dlc_output_{bodypart}": eddie_active_projects / "Wolf/MMNAV/derivatives" / f"M{mouse:02d}/D{day:02d}/{session}/"}

    uv_directory = "/exports/eddie/scratch/chalcrow/code/nolanlab-dlc/"
    python_arg = f"pose_estimation.py {mouse} {day} {session} {bodypart} --data_folder {data_folder} --deriv_folder {deriv_folder}"

    run_stage_script(stagein_dict, job_name=stagein_job_name)
    run_python_script(uv_directory, python_arg, cores=8, email="chalcrow@ed.ac.uk", staging=False, hold_jid=stagein_job_name, job_name=run_python_name)
    run_stage_script(stageout_dict, job_name=stageout_job_name, hold_jid=run_python_name)

if __name__ == "__main__":
    main()
