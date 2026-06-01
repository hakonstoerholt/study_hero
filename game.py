"""Game math: leveling curve and battle damage. Pure functions, no state."""

PLAYER_HP_MAX = 100
WRONG_DAMAGE = 15          # HP the player loses on a wrong answer
MONSTER_HP_PER_Q = 10      # monster max HP = questions * this


def xp_for(difficulty):
    """XP earned for a correct answer of the given difficulty (1-5)."""
    return 10 * max(1, min(5, difficulty))


def damage_for(difficulty):
    """Damage a correct answer deals to the monster."""
    return 10 + 2 * max(1, min(5, difficulty))


def xp_to_reach(level):
    """Total XP needed to reach a given level (level 1 starts at 0)."""
    # cumulative of 100, 150, 200, ... -> a gentle quadratic curve
    n = level - 1
    return 50 * n * (n + 1) // 2 + 50 * n


def level_state(total_xp):
    """Return (level, xp_into_level, xp_needed_for_next_level)."""
    level = 1
    while xp_to_reach(level + 1) <= total_xp:
        level += 1
    base = xp_to_reach(level)
    nxt = xp_to_reach(level + 1)
    return level, total_xp - base, nxt - base
