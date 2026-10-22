@echo off
rem Run by pixi on activation (Windows). Chooses the ROS domain and the Cyclone DDS config.
rem "pixi run robot on" creates .ros_robot: domain 30 and the robot as a discovery peer.
rem Otherwise the domain is derived from the computer name (31..130) so that Windows PCs on
rem the same Wi-Fi do not see each other's simulators (discovery uses multicast on Windows).
set "_root=%PIXI_PROJECT_ROOT:\=/%"
if exist "%PIXI_PROJECT_ROOT%\.ros_robot" (
  set "ROS_DOMAIN_ID=30"
  set "CYCLONEDDS_URI=file://%_root%/scripts/cyclonedds-windows-robot.xml"
) else (
  for /f %%i in ('powershell -NoProfile -Command "$s=0; foreach($c in [char[]]$env:COMPUTERNAME){$s+=[int]$c}; 31 + ($s %% 100)"') do set "ROS_DOMAIN_ID=%%i"
  set "CYCLONEDDS_URI=file://%_root%/scripts/cyclonedds-windows.xml"
)
if "%ROS_DOMAIN_ID%"=="" set "ROS_DOMAIN_ID=30"
set "_root="
