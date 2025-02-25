"""Simplest example of files_dropdown_menu + notification."""

from contextlib import asynccontextmanager
import os
from pathlib import Path
import tempfile
from typing import Annotated

import imageio
import numpy
from fastapi import BackgroundTasks, Depends, FastAPI, responses
from pygifsicle import optimize

from nc_py_api import FsNode, NextcloudApp
from nc_py_api.ex_app import AppAPIAuthMiddleware, LogLvl, nc_app, run_app, set_handlers
from nc_py_api.files import ActionFileInfoEx


@asynccontextmanager
async def lifespan(app: FastAPI):
    set_handlers(app, enabled_handler)
    yield


APP = FastAPI(lifespan=lifespan)
APP.add_middleware(AppAPIAuthMiddleware)  # set global AppAPI authentication middleware


def convert_video_to_gif(input_file: FsNode, nc: NextcloudApp):
    save_path = os.path.splitext(input_file.user_path)[0] + ".gif"
    nc.log(LogLvl.WARNING, f"Processing:{input_file.user_path} -> {save_path}")
    try:
        with tempfile.NamedTemporaryFile(mode="w+b") as tmp_in:
            nc.files.download2stream(input_file, tmp_in)
            nc.log(LogLvl.WARNING, "File downloaded")
            tmp_in.flush()
            cap = cv2.VideoCapture(tmp_in.name)
            with tempfile.NamedTemporaryFile(mode="w+b", suffix=".gif") as tmp_out:
                image_lst = []
                previous_frame = None
                skip = 0
                while True:
                    skip += 1
                    ret, frame = cap.read()
                    if frame is None:
                        break
                    if skip == 2:
                        skip = 0
                        continue
                    if previous_frame is not None:
                        diff = numpy.mean(previous_frame != frame)
                        if diff < 0.91:
                            continue
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    image_lst.append(frame_rgb)
                    previous_frame = frame
                    if len(image_lst) > 60:
                        break
                cap.release()
                imageio.mimsave(tmp_out.name, image_lst)
                optimize(tmp_out.name)
                nc.log(LogLvl.WARNING, "GIF is ready")
                nc.files.upload_stream(save_path, tmp_out)
                nc.log(LogLvl.WARNING, "Result uploaded")
                nc.notifications.create(f"{input_file.name} finished!", f"{save_path} is waiting for you!")
    except Exception as e:
        nc.log(LogLvl.ERROR, str(e))
        nc.notifications.create("Error occurred", "Error information was written to log file")


@APP.post("/video_to_gif")
async def video_to_gif(
    files: ActionFileInfoEx,
    nc: Annotated[NextcloudApp, Depends(nc_app)],
    background_tasks: BackgroundTasks,
):
    for one_file in files.files:
        background_tasks.add_task(convert_video_to_gif, one_file.to_fs_node(), nc)
    return responses.Response()


def enabled_handler(enabled: bool, nc: NextcloudApp) -> str:
    # This will be called each time application is `enabled` or `disabled`
    # NOTE: `user` is unavailable on this step, so all NC API calls that require it will fail as unauthorized.
    print(f"enabled={enabled}")
    try:
        if enabled:
            nc.ui.files_dropdown_menu.register_ex(
                "to_gif",
                "To GIF",
                "/video_to_gif",
                mime="video",
                icon="img/icon.svg",
            )
            nc.log(LogLvl.WARNING, f"Hello from {nc.app_cfg.app_name} :)")
        else:
            nc.log(LogLvl.WARNING, f"Bye bye from {nc.app_cfg.app_name} :(")
    except Exception as e:
        # In case of an error, a non-empty short string should be returned, which will be shown to the NC administrator.
        return str(e)
    return ""


if __name__ == "__main__":
    # Wrapper around `uvicorn.run`.
    # You are free to call it directly, with just using the `APP_HOST` and `APP_PORT` variables from the environment.
    os.chdir(Path(__file__).parent)
    run_app("main:APP", log_level="trace")