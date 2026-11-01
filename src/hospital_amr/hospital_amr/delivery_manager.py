#!/usr/bin/env python3
"""
delivery_manager.py — Hospital Medicine Delivery Manager.

Manages the full delivery workflow:
  1. Receives a delivery request (bed ID)
  2. Waits for Nav2 to be fully active
  3. Navigates to the bed
  4. Confirms delivery
  5. Returns to the pharmacy

Usage:
  ros2 run hospital_amr delivery_manager --ros-args -p bed_id:=bed_01
"""

import rclpy
from rclpy.node import Node
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import String
import math
import time
from enum import Enum
from datetime import datetime

from hospital_amr.bed_registry import BedRegistry


class MissionState(Enum):
    IDLE = "IDLE"
    REQUEST_RECEIVED = "REQUEST_RECEIVED"
    NAVIGATING_TO_BED = "NAVIGATING_TO_BED"
    ARRIVED_AT_BED = "ARRIVED_AT_BED"
    DELIVERY_CONFIRMED = "DELIVERY_CONFIRMED"
    RETURNING_TO_PHARMACY = "RETURNING_TO_PHARMACY"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class DeliveryManager(Node):
    """Manages medicine delivery missions."""

    def __init__(self):
        super().__init__('delivery_manager')

        # --- Parameters ---
        self.declare_parameter('bed_id', 'bed_01')
        self.declare_parameter('medicine_id', 'MED-DEFAULT')

        self.bed_id = self.get_parameter('bed_id').get_parameter_value().string_value
        self.medicine_id = self.get_parameter('medicine_id').get_parameter_value().string_value

        # --- Components ---
        self.registry = BedRegistry()
        self.navigator = BasicNavigator()

        # --- State ---
        self.state = MissionState.IDLE
        self.mission_log = []

        # --- Publishers ---
        self.status_pub = self.create_publisher(String, '/delivery_status', 10)

        self.get_logger().info('╔══════════════════════════════════════╗')
        self.get_logger().info('║   Hospital Delivery Manager          ║')
        self.get_logger().info('╚══════════════════════════════════════╝')
        self.get_logger().info(f'Target: {self.bed_id}')
        self.get_logger().info(f'Medicine: {self.medicine_id}')

    def set_state(self, new_state: MissionState):
        """Transition to a new mission state and log it."""
        old = self.state
        self.state = new_state
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.mission_log.append({
            'time': timestamp,
            'from': old.value,
            'to': new_state.value,
        })
        self.get_logger().info(f'State: {old.value} → {new_state.value}')
        status = String()
        status.data = f'{new_state.value}: {self.bed_id}'
        self.status_pub.publish(status)

    def create_pose(self, x: float, y: float, yaw: float = 0.0) -> PoseStamped:
        """Create a PoseStamped for Nav2."""
        pose = PoseStamped()
        pose.header.frame_id = 'map'
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.position.z = 0.0
        pose.pose.orientation.z = math.sin(yaw / 2.0)
        pose.pose.orientation.w = math.cos(yaw / 2.0)
        return pose

    def navigate_to(self, x: float, y: float, yaw: float,
                    label: str) -> bool:
        """Navigate to a position using Nav2. Returns True on success."""
        self.get_logger().info(f'Navigating to {label}: ({x:.1f}, {y:.1f})')
        goal = self.create_pose(x, y, yaw)
        self.navigator.goToPose(goal)

        while not self.navigator.isTaskComplete():
            feedback = self.navigator.getFeedback()
            if feedback:
                dist = feedback.distance_remaining
                self.get_logger().info(
                    f'  → {label}: {dist:.2f}m remaining',
                    throttle_duration_sec=3.0)
            time.sleep(0.5)

        result = self.navigator.getResult()
        if result == TaskResult.SUCCEEDED:
            self.get_logger().info(f'  ✅ Arrived at {label}!')
            return True
        elif result == TaskResult.CANCELED:
            self.get_logger().warning(f'  ⚠ Navigation to {label} cancelled')
            return False
        else:
            self.get_logger().error(f'  ❌ Navigation to {label} FAILED')
            return False

    def run_delivery(self):
        """Execute the full delivery mission."""

        start_time = datetime.now()

        # --- 1. Validate request ---
        self.set_state(MissionState.REQUEST_RECEIVED)
        bed = self.registry.get_bed(self.bed_id)
        if bed is None:
            self.get_logger().error(f'❌ Unknown bed: {self.bed_id}')
            self.get_logger().info(
                f'Available beds: {", ".join(self.registry.list_beds())}')
            self.set_state(MissionState.FAILED)
            return

        self.get_logger().info(f'Delivery request validated:')
        self.get_logger().info(f'  Bed: {bed["name"]}')
        self.get_logger().info(f'  Room: {bed["room"]}')
        self.get_logger().info(f'  Medicine: {self.medicine_id}')
        self.get_logger().info(f'  Position: ({bed["x"]}, {bed["y"]})')

        # --- 2. Wait for Nav2 ---
        self.get_logger().info('Waiting for Nav2 to be fully ready...')
        self.navigator.waitUntilNav2Active()
        self.get_logger().info('Nav2 is active!')

        # --- 3. Set initial pose at pharmacy ---
        pharmacy = self.registry.get_pharmacy()
        initial = self.create_pose(pharmacy['x'], pharmacy['y'],
                                    pharmacy.get('yaw', 0.0))
        self.navigator.setInitialPose(initial)
        self.get_logger().info('Initial pose set at Pharmacy. Waiting for AMCL...')
        time.sleep(3.0)  # Let AMCL converge

        # --- 4. Navigate to bed ---
        self.set_state(MissionState.NAVIGATING_TO_BED)
        success = self.navigate_to(
            bed['x'], bed['y'], bed['yaw'], bed['name'])

        if not success:
            self.set_state(MissionState.FAILED)
            return

        # --- 5. Arrived — confirm delivery ---
        self.set_state(MissionState.ARRIVED_AT_BED)
        self.get_logger().info(f'📦 Delivering {self.medicine_id} to {bed["name"]}...')
        time.sleep(2.0)  # Simulated delivery time

        self.set_state(MissionState.DELIVERY_CONFIRMED)
        self.get_logger().info(f'✅ Delivery confirmed at {bed["name"]}!')

        # --- 6. Return to pharmacy ---
        self.set_state(MissionState.RETURNING_TO_PHARMACY)
        success = self.navigate_to(
            pharmacy['x'], pharmacy['y'],
            pharmacy.get('yaw', 0.0), 'Pharmacy')

        self.set_state(MissionState.COMPLETED)

        # --- 7. Mission summary ---
        elapsed = (datetime.now() - start_time).total_seconds()
        self.get_logger().info('')
        self.get_logger().info('╔══════════════════════════════════════╗')
        self.get_logger().info('║        MISSION SUMMARY               ║')
        self.get_logger().info('╠══════════════════════════════════════╣')
        self.get_logger().info(f'║ Bed:      {bed["name"]:<28}║')
        self.get_logger().info(f'║ Medicine: {self.medicine_id:<28}║')
        self.get_logger().info(f'║ Status:   ✅ DELIVERED{" " * 17}║')
        self.get_logger().info(f'║ Time:     {elapsed:.1f}s{" " * (26 - len(f"{elapsed:.1f}s"))}║')
        self.get_logger().info('╚══════════════════════════════════════╝')


def main(args=None):
    rclpy.init(args=args)
    node = DeliveryManager()

    try:
        node.run_delivery()
    except KeyboardInterrupt:
        node.get_logger().info('Mission interrupted!')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
