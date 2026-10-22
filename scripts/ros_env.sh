# Sourced by pixi on activation (macOS/Linux). Sets the ROS domain from .ros_domain_id.
_domain_file="${PIXI_PROJECT_ROOT:-.}/.ros_domain_id"
if [ -f "$_domain_file" ]; then
  export ROS_DOMAIN_ID="$(tr -dc '0-9' < "$_domain_file")"
fi
export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-30}"
# All PCs use the normal discovery range; separation between students is done by ROS_DOMAIN_ID.
export ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET
unset _domain_file
