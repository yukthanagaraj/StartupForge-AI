import random
from typing import Dict, Any, Tuple

RANDOM_EVENTS = [
    {
        "title": "Viral Product Hunt Launch",
        "description": "Your product gets hunted! An influx of early adopters discover your service.",
        "effect": {"users": 1200, "mrr": 4500.0, "valuation": 25000.0, "budget": 1000.0},
        "type": "positive"
    },
    {
        "title": "AWS Server Crash",
        "description": "A database node runs out of memory. Uptime drops, and users are frustrated.",
        "effect": {"users": -150, "mrr": -600.0, "code_quality": -5.0, "tech_debt": 8.0, "budget": -350.0},
        "type": "negative"
    },
    {
        "title": "Angel Investor Pitch Success",
        "description": "An angel investor is impressed by your interactive agent demonstration and writes a check!",
        "effect": {"budget": 15000.0, "valuation": 40000.0},
        "type": "positive"
    },
    {
        "title": "Technical Debt Backlash",
        "description": "Legacy code blocks a hotfix deployment. The developer has to work overtime.",
        "effect": {"tech_debt": 15.0, "code_quality": -8.0, "energy_Dev": -25},
        "type": "negative"
    },
    {
        "title": "Dev Caching Breakthrough",
        "description": "Your developer rewrites a slow SQL join into a Redis cache. API speeds double!",
        "effect": {"code_quality": 12.0, "tech_debt": -10.0, "valuation": 5000.0},
        "type": "positive"
    },
    {
        "title": "Growth Hack Experiment",
        "description": "Your marketer launches a viral memetic campaign on X (Twitter). Click rates skyrocket.",
        "effect": {"users": 450, "mrr": 1800.0, "budget": -200.0},
        "type": "positive"
    }
]

class StartupSimulation:
    """Calculates all math and business mechanics for the startup forge simulator."""

    @staticmethod
    def calculate_burn_rate(state: Dict[str, Any]) -> float:
        """Calculates daily burn rate based on agent levels and codebase debt."""
        base_burn = 150.0 # Standard hosting & operating cost
        agent_costs = sum(
            agent.get("level", 1) * 75.0 for agent in state["agents"].values()
        )
        debt_penalty = state.get("tech_debt", 0.0) * 2.5 # Tech debt costs hosting money!
        return base_burn + agent_costs + debt_penalty

    @staticmethod
    def tick_day(state: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
        """Ticks the simulator by 1 day. Deducts burn rate, adds MRR/30 to budget, updates valuation."""
        # Increments day
        state["day"] += 1
        day_str = f"Day {state['day']}"

        # Financial formulas
        burn = StartupSimulation.calculate_burn_rate(state)
        mrr = state.get("mrr", 0.0)
        daily_revenue = mrr / 30.0
        
        # Deduct burn and add revenue
        net_flow = daily_revenue - burn
        state["budget"] = round(state["budget"] + net_flow, 2)

        # Regulate user count decay & conversion rates
        users = state.get("users", 0)
        if users > 0:
            # Slight natural churn if code quality is poor
            churn_rate = 0.01 + (100.0 - state.get("code_quality", 100.0)) * 0.001
            churned = int(users * churn_rate)
            state["users"] = max(0, users - churned)
            state["mrr"] = round(state["users"] * 4.0, 2) # Assume average $4 ARPU

        # Valuation metric model
        # Valuation = (MRR * 12 * 8) + (Code Quality * 100) - (Tech Debt * 50) + Budget
        val_revenue_multiplier = state.get("mrr", 0.0) * 12.0 * 5.0
        val_code_multiplier = state.get("code_quality", 100.0) * 150.0
        val_debt_penalty = state.get("tech_debt", 0.0) * 100.0
        calculated_valuation = max(
            1000.0, 
            val_revenue_multiplier + val_code_multiplier - val_debt_penalty + state["budget"]
        )
        state["valuation"] = round(calculated_valuation, 2)

        # Recover agent energy slightly overnight (sleep)
        for agent_name, agent_data in state["agents"].items():
            agent_data["energy"] = min(100, agent_data["energy"] + random.randint(15, 25))

        # Check for random events (15% chance per day)
        event_msg = ""
        if random.random() < 0.15:
            state, event_msg = StartupSimulation.trigger_random_event(state, day_str)

        return state, event_msg

    @staticmethod
    def trigger_random_event(state: Dict[str, Any], day_str: str) -> Tuple[Dict[str, Any], str]:
        """Triggers a random event, applies its numerical effects, and logs the result."""
        event = random.choice(RANDOM_EVENTS)
        effects = event["effect"]
        
        # Apply effects
        if "users" in effects:
            state["users"] = max(0, state.get("users", 0) + effects["users"])
            state["mrr"] = round(state["users"] * 4.0, 2)
        if "mrr" in effects:
            state["mrr"] = round(max(0.0, state.get("mrr", 0.0) + effects["mrr"]), 2)
        if "budget" in effects:
            state["budget"] = round(max(0.0, state.get("budget", 0.0) + effects["budget"]), 2)
        if "valuation" in effects:
            state["valuation"] = round(max(1000.0, state.get("valuation", 0.0) + effects["valuation"]), 2)
        if "code_quality" in effects:
            state["code_quality"] = round(max(10.0, min(100.0, state.get("code_quality", 100.0) + effects["code_quality"])), 2)
        if "tech_debt" in effects:
            state["tech_debt"] = round(max(0.0, state.get("tech_debt", 0.0) + effects["tech_debt"]), 2)
            
        # Agent specific energy effects
        for key, val in effects.items():
            if key.startswith("energy_"):
                agent_name = key.split("_")[1]
                if agent_name in state["agents"]:
                    state["agents"][agent_name]["energy"] = max(10, min(100, state["agents"][agent_name]["energy"] + val))

        # Add event log
        marker = "🟢 SUCCESS" if event["type"] == "positive" else "🔴 INCIDENT"
        log_entry = {
            "sender": "System",
            "message": f"[{marker}] {event['title']}: {event['description']}",
            "timestamp": day_str
        }
        state["logs"].append(log_entry)
        
        event_banner = f"{marker} | {event['title']}\n{event['description']}"
        return state, event_banner
