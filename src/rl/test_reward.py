import os
import sys

# Ensure the current directory is in Python's search path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from reward import RewardFunction

def print_scenario(name, reward, components, explanation):
    print("=" * 80)
    print(f"SCENARIO: {name}")
    print("-" * 80)
    print(f"Explanation: {explanation}")
    print(f"Total Step Reward: {reward:+.2f}")
    print("Reward Components Breakdown:")
    for comp, value in components.items():
        print(f"  - {comp:<20}: {value:+.2f}")
    print("=" * 80)
    print()

def main():
    print("Running Phase 7 Reward System Scenarios Test...\n")
    
    # Initialize the reward function class
    reward_fn = RewardFunction()
    
    # ----------------------------------------------------
    # Scenario A: Safe Flight (Straight towards Waypoint)
    # ----------------------------------------------------
    r_a, comp_a = reward_fn.calculate_total_reward(
        action=1,                        # Straight (stable flight)
        curr_dist_to_waypoint=95.0,      # Closer to waypoint
        prev_dist_to_waypoint=100.0,     # Previous distance
        waypoint_reached=False,
        curr_dist_to_missile=9999.0,
        prev_dist_to_missile=9999.0,
        missile_active=False,
        missile_evaded=False,
        collision_detected=False,
        wrapped=False,
        missile_hit=False
    )
    # Expected: Survival (+1) + Stable flight (+5) + Waypoint progress (+1) = +7.0
    print_scenario(
        "Scenario A: Safe Flight (Straight towards Waypoint)",
        r_a, comp_a,
        "The aircraft is flying straight (stable flight, +5) and moving closer to the waypoint (+1). "
        "It also gets the base survival reward (+1). Expected total: +7.0"
    )
    assert r_a == 7.0, f"Expected 7.0, got {r_a}"

    # ----------------------------------------------------
    # Scenario B: Waypoint Reached
    # ----------------------------------------------------
    r_b, comp_b = reward_fn.calculate_total_reward(
        action=1,                        # Straight
        curr_dist_to_waypoint=10.0,
        prev_dist_to_waypoint=20.0,
        waypoint_reached=True,
        curr_dist_to_missile=9999.0,
        prev_dist_to_missile=9999.0,
        missile_active=False,
        missile_evaded=False,
        collision_detected=False,
        wrapped=False,
        missile_hit=False
    )
    # Expected: Survival (+1) + Stable flight (+5) + Reach waypoint (+15) = +21.0
    print_scenario(
        "Scenario B: Waypoint Reached",
        r_b, comp_b,
        "The aircraft flies straight (+5) and successfully reaches the waypoint (+15) while "
        "surviving the step (+1). Expected total: +21.0"
    )
    assert r_b == 21.0, f"Expected 21.0, got {r_b}"

    # ----------------------------------------------------
    # Scenario C: Missile Evaded
    # ----------------------------------------------------
    r_c, comp_c = reward_fn.calculate_total_reward(
        action=0,                        # Turning left (trying to dodge)
        curr_dist_to_waypoint=120.0,     # Moving farther from waypoint during evade
        prev_dist_to_waypoint=115.0,
        waypoint_reached=False,
        curr_dist_to_missile=310.0,      # Moving farther from missile
        prev_dist_to_missile=300.0,
        missile_active=True,
        missile_evaded=True,
        collision_detected=False,
        wrapped=False,
        missile_hit=False
    )
    # Expected: Survival (+1) + Turn penalty (-0.5) + Waypoint regress (-1.0) + Evade missile (+30.0) = +29.5
    print_scenario(
        "Scenario C: Missile Evaded",
        r_c, comp_c,
        "The aircraft is turning to evade (-0.5), which moves it away from the waypoint (-1.0). "
        "However, it survives (+1) and successfully evades the missile threat (+30.0). Expected total: +29.5"
    )
    assert r_c == 29.5, f"Expected 29.5, got {r_c}"

    # ----------------------------------------------------
    # Scenario D: Obstacle Collision
    # ----------------------------------------------------
    r_d, comp_d = reward_fn.calculate_total_reward(
        action=1,                        # Straight
        curr_dist_to_waypoint=100.0,
        prev_dist_to_waypoint=100.0,
        waypoint_reached=False,
        curr_dist_to_missile=9999.0,
        prev_dist_to_missile=9999.0,
        missile_active=False,
        missile_evaded=False,
        collision_detected=True,
        wrapped=False,
        missile_hit=False
    )
    # Expected: Survival (+1) + Stable flight (+5) + Waypoint regress/neutral (-1) + Collision penalty (-50) = -45.0
    print_scenario(
        "Scenario D: Obstacle Collision",
        r_d, comp_d,
        "The aircraft is flying straight (+5) and survives (+1), but hits an obstacle (-50) "
        "and makes no progress to the waypoint (-1). Expected total: -45.0"
    )
    assert r_d == -45.0, f"Expected -45.0, got {r_d}"

    # ----------------------------------------------------
    # Scenario E: Missile Hit
    # ----------------------------------------------------
    r_e, comp_e = reward_fn.calculate_total_reward(
        action=2,                        # Turning right
        curr_dist_to_waypoint=100.0,
        prev_dist_to_waypoint=100.0,
        waypoint_reached=False,
        curr_dist_to_missile=12.0,       # Closer to missile
        prev_dist_to_missile=20.0,
        missile_active=True,
        missile_evaded=False,
        collision_detected=False,
        wrapped=False,
        missile_hit=True
    )
    # Expected: Survival (+1) + Turn penalty (-0.5) + Waypoint regress (-1.0) + Closer to missile (-1.5) + Hit penalty (-100) = -102.0
    print_scenario(
        "Scenario E: Missile Hit",
        r_e, comp_e,
        "The aircraft was turning (-0.5), moving away from the waypoint (-1.0), moving closer to the "
        "missile (-1.5), and was hit by the missile (-100), although it survived the frame update itself (+1). "
        "Expected total: -102.0"
    )
    assert r_e == -102.0, f"Expected -102.0, got {r_e}"

    # ----------------------------------------------------
    # Scenario F: Boundary Violation
    # ----------------------------------------------------
    r_f, comp_f = reward_fn.calculate_total_reward(
        action=1,                        # Straight
        curr_dist_to_waypoint=100.0,
        prev_dist_to_waypoint=100.0,
        waypoint_reached=False,
        curr_dist_to_missile=9999.0,
        prev_dist_to_missile=9999.0,
        missile_active=False,
        missile_evaded=False,
        collision_detected=False,
        wrapped=True,
        missile_hit=False
    )
    # Expected: Survival (+1) + Stable flight (+5) + Waypoint regress/neutral (-1) + Boundary penalty (-20) = -15.0
    print_scenario(
        "Scenario F: Boundary Violation",
        r_f, comp_f,
        "The aircraft is flying straight (+5) but leaves the environment boundary, causing "
        "a wrap-around penalty (-20). It also gets the survival reward (+1) and waypoint neutral penalty (-1). "
        "Expected total: -15.0"
    )
    assert r_f == -15.0, f"Expected -15.0, got {r_f}"

    print("All scenario assertions passed successfully!")

if __name__ == '__main__':
    main()
