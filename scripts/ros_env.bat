@echo off
rem Run by pixi on activation (Windows). Chooses the Cyclone DDS config file.
rem "pixi run robot on" creates .ros_robot, which adds the TurtleBot3 as a peer.
rem On Windows, Cyclone cannot send to 127.0.0.1 from a socket bound to the network
rem adapter, so this PC's own name (which resolves to the adapter address) is added as a
rem peer through an inline config fragment appended after the file.
set "_root=%PIXI_PROJECT_ROOT:\=/%"
if exist "%PIXI_PROJECT_ROOT%\.ros_robot" (
  set "_file=cyclonedds-robot.xml"
) else (
  set "_file=cyclonedds.xml"
)
set "CYCLONEDDS_URI=file://%_root%/scripts/%_file%,<CycloneDDS><Domain Id='any'><Discovery><Peers><Peer address='%COMPUTERNAME%'/></Peers></Discovery></Domain></CycloneDDS>"
set "_root="
set "_file="
