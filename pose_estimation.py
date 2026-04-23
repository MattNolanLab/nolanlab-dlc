"""
This script is the pipeline step:

|-----------|            |--------------|
|   video   |    --->    |  dlc output  |
|-----------|            |--------------|

It can be called from the command line. An example:

uv run sort_on_comp.py --mouse 6 --day 12 --session OF1 --bodypart body --data_folder /home/nolanlab/Work/Harry_Project/data/ --deriv_folder /home/nolanlab/Work/Harry_Project/derivatives/

This will take the video data for mouse "6" on day "12" for the session "OF1",
and apply the `of_cohort12-krs-2024-10-30` dlc model to it.

We expect the data to be stored in the form

data_folder/
    global_session_type/
        M{mouse:02d}_D{day:02d}_*_{session_type}/
            M{mouse:02d}_D{day:02d}_{session_type}_*.avi

And the output data will be stored in the form

deriv_folder/
    M{mouse:02d}/
        D{day:02d}/
            {session_type}/
                dlc_output_{bodypart}/
                    lots
                    of
                    output
                    from
                    dlc
"""

import os
import shutil
from argparse import ArgumentParser
from pathlib import Path

import cv2
import deeplabcut as dlc
import pandas as pd


def make_cropped_video(video_path, output_path, cropping):
    if cropping is None:
        _ = shutil.copy(video_path, output_path)

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)

    # Initialize frame counter
    cnt = 0

    x, y, w, h = cropping

    fourcc = cv2.VideoWriter_fourcc(*"XVID")
    out = cv2.VideoWriter(output_path, fourcc, fps, (w, h))

    # Now we start
    while cap.isOpened():
        ret, frame = cap.read()

        cnt += 1

        if ret == True:
            crop_frame = frame[y : y + h, x : x + w]

            out.write(crop_frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
        else:
            break

    cap.release()
    out.release()
    cv2.destroyAllWindows()


def main():
    parser = ArgumentParser()

    parser.add_argument("mouse")
    parser.add_argument("day")
    parser.add_argument("session")
    parser.add_argument("bodypart")
    parser.add_argument("--data_folder", default=None)
    parser.add_argument("--deriv_folder", default=None)

    mouse = int(parser.parse_args().mouse)
    day = int(parser.parse_args().day)
    session = parser.parse_args().session
    bodypart = parser.parse_args().bodypart

    if bodypart not in ["tongue", "eye", "body"]:
        raise UserWarning("bodypart must be lick eye or body!")

    data_folder = parser.parse_args().data_folder
    if data_folder is None:
        data_folder = "/exports/eddie/scratch/chalcrow/wolf/data"
    data_folder = Path(data_folder)

    deriv_folder = parser.parse_args().deriv_folder
    if deriv_folder is None:
        deriv_folder = "/exports/eddie/scratch/chalcrow/wolf/derivatives"
    deriv_folder = Path(deriv_folder)

    if bodypart == "tongue":
        config_path = "/exports/eddie/scratch/chalcrow/wolf/code/models/c12_lick-chris-2024-10-03/config.yaml"
    elif bodypart == "eye":
        config_path = "/exports/eddie/scratch/chalcrow/wolf/code/models/vr-hc-2024-03-14_eddie/config.yaml"
    elif bodypart == "body":
        config_path = "/exports/eddie/scratch/chalcrow/wolf/code/models/of_cohort12-krs-2024-10-30/config.yaml"

    mouse_day_session_folder = list(
        data_folder.glob(f"M{mouse:02d}_D{day:02d}_*{session}")
    )[0]

    if bodypart in ["eye", "tongue"]:
        video_path = str(
            mouse_day_session_folder
            / f"M{mouse:02d}_D{day:02d}_{session}_side_capture.avi"
        )
    else:
        video_path = str(
            mouse_day_session_folder / f"M{mouse:02d}_D{day:02d}_{session}.avi"
        )

    save_path = (
        deriv_folder / f"M{mouse:02d}/D{day:02d}/{session}/dlc_output_{bodypart}/"
    )
    save_path.mkdir(parents=True, exist_ok=True)
    cropped_video_path = str(
        save_path / f"M{mouse:02d}_D{day:02d}_{session}_side_capture_{bodypart}.avi"
    )

    if bodypart in ["eye", "tongue"]:
        all_crop_info = pd.read_csv(f"wolf_crops/{bodypart}_crops_wolf.csv")
        mouseday_crops = all_crop_info.query(f"mouse == {mouse} & day == {day}")
        if len(mouseday_crops) > 0:
            x, y, w, h = mouseday_crops[["x", "y", "w", "h"]].values[0]
        else:
            # if we've not done manual crops, use the last day.
            x, y, w, h = (
                all_crop_info.query(f"mouse == {mouse}")
                .sort_values("day")
                .iloc[-1][["x", "y", "w", "h"]]
                .values
            )
        cropping = [x, y, w, h]
    else:
        cropping = None

    make_cropped_video(video_path, cropped_video_path, cropping)

    dlc.analyze_videos(
        config_path,
        [cropped_video_path],
        save_as_csv=True,
        destfolder=save_path,
    )
    dlc.filterpredictions(config_path, [cropped_video_path])
    dlc.create_labeled_video(config_path, [cropped_video_path], save_frames=False)
    dlc.plot_trajectories(config_path, [cropped_video_path])

    os.remove(cropped_video_path)


if __name__ == "__main__":
    main()
