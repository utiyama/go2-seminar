# Sourced by pixi on activation (macOS/Linux). Sets the ROS domain and the Cyclone DDS config.
# Multicast is disabled (see scripts/cyclonedds*.xml); only listed peers are discovered, so
# simulators on different PCs never see each other and everyone can stay on domain 30.
# "pixi run robot on" creates .ros_robot, which adds the TurtleBot3 as a peer.
_root="${PIXI_PROJECT_ROOT:-.}"
export ROS_DOMAIN_ID=30
if [ -f "$_root/.ros_robot" ]; then
  export CYCLONEDDS_URI="file://$_root/scripts/cyclonedds-robot.xml"
else
  export CYCLONEDDS_URI="file://$_root/scripts/cyclonedds.xml"
fi
unset _root
