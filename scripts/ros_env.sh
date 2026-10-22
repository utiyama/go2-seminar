# Sourced by pixi on activation (macOS/Linux). Chooses the Cyclone DDS config file.
# Multicast is disabled (see scripts/cyclonedds*.xml); only listed peers are discovered.
# "pixi run robot on" creates .ros_robot, which adds the TurtleBot3 as a peer.
_root="${PIXI_PROJECT_ROOT:-.}"
if [ -f "$_root/.ros_robot" ]; then
  export CYCLONEDDS_URI="file://$_root/scripts/cyclonedds-robot.xml"
else
  export CYCLONEDDS_URI="file://$_root/scripts/cyclonedds.xml"
fi
unset _root
