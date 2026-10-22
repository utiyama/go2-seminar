@echo off
rem Run by pixi on activation (Windows). Sets the ROS domain from .ros_domain_id.
if exist "%PIXI_PROJECT_ROOT%\.ros_domain_id" (
  set /p ROS_DOMAIN_ID=<"%PIXI_PROJECT_ROOT%\.ros_domain_id"
)
if "%ROS_DOMAIN_ID%"=="" set ROS_DOMAIN_ID=30
set ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET
