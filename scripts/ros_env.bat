@echo off
rem Run by pixi on activation (Windows). Chooses the Cyclone DDS config file.
rem "pixi run robot on" creates .ros_robot, which adds the TurtleBot3 as a peer.
set "_root=%PIXI_PROJECT_ROOT:\=/%"
if exist "%PIXI_PROJECT_ROOT%\.ros_robot" (
  set "CYCLONEDDS_URI=file://%_root%/scripts/cyclonedds-robot.xml"
) else (
  set "CYCLONEDDS_URI=file://%_root%/scripts/cyclonedds.xml"
)
set "_root="
