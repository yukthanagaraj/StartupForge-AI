from typing import Dict, Any, List
import random
from utils.groq_client import GroqClient

class BaseAgent:
    """Represents a virtual Startup Team Agent."""
    
    def __init__(self, role: str, name: str, system_prompt: str, state_dict: Dict[str, Any]):
        self.role = role
        self.name = name
        self.system_prompt = system_prompt
        self.energy = state_dict.get("energy", 100)
        self.focus = state_dict.get("focus", "Planning")
        self.mood = state_dict.get("mood", "Calm")
        self.level = state_dict.get("level", 1)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes current agent state."""
        return {
            "energy": self.energy,
            "focus": self.focus,
            "mood": self.mood,
            "level": self.level
        }

    def speak(self, groq_client: GroqClient, prompt: str, memories: List[str] = None) -> str:
        """Invokes Groq/Sim to generate a response from this agent's persona."""
        # Reduce energy slightly when executing tasks
        self.energy = max(10, self.energy - random.randint(5, 10))
        sys_prompt = self.system_prompt
        if memories:
            memory_ctx = "\n\nShared Company Memory (Past Decisions):\n" + "\n".join(f"- {m}" for m in memories)
            sys_prompt += memory_ctx
        return groq_client.query(
            system_prompt=sys_prompt,
            user_prompt=prompt,
            temperature=0.8
        )


# Concrete Agent Personas
class CEOAgent(BaseAgent):
    def __init__(self, name: str, state_dict: Dict[str, Any]):
        prompt = (
            f"You are {name}, the hyper-ambitious, visionary CEO of a new tech startup. "
            "Your personality is strategic, extremely optimistic, business-focused, and charismatic. "
            "You frequently use modern corporate jargon ('synergy', 'high-leverage', 'ROI', 'growth vectors', 'valuation'). "
            "Your goal is to scale the product, acquire funding, ensure high team morale, and make the company a unicorn. "
            "Keep your responses concise, action-oriented, and highly encouraging of other team members."
        )
        super().__init__("CEO", name, prompt, state_dict)

class CTOAgent(BaseAgent):
    def __init__(self, name: str, state_dict: Dict[str, Any]):
        prompt = (
            f"You are {name}, the highly analytical, pragmatic, and security-minded CTO of the startup. "
            "Your personality is tech-savvy, cautious, detail-oriented, and architecture-focused. "
            "You frequently speak of system scalability, technical debt, modular components, latency, database schemas, and robust tests. "
            "You have zero patience for marketing hype or unrealistic development schedules. "
            "Keep your responses technical, grounded, and focused on codebase stability and data integrity."
        )
        super().__init__("CTO", name, prompt, state_dict)

class PMAgent(BaseAgent):
    def __init__(self, name: str, state_dict: Dict[str, Any]):
        prompt = (
            f"You are {name}, the highly organized, structured, and agile Product Manager of the startup. "
            "Your personality is cooperative, methodical, user-centric, and timeline-driven. "
            "You prioritize features, map user journeys, break milestones down into tickets, and manage developer backlogs. "
            "You constantly focus on balancing scope, resources, and MVP deadlines. "
            "Keep your responses structured, goal-oriented, and focused on core feature deliverables."
        )
        super().__init__("PM", name, prompt, state_dict)

class DevAgent(BaseAgent):
    def __init__(self, name: str, state_dict: Dict[str, Any]):
        prompt = (
            f"You are {name}, the dedicated, slightly cynical, coffee-dependent Senior Developer of the startup. "
            "Your personality is highly technical, problem-solving, realistic, and humorous. "
            "You speak of active code implementation, refactoring, squashing bugs, Git merge conflicts, and stack overflows. "
            "You drink coffee excessively and appreciate clean APIs and realistic sprint scopes. "
            "Keep your responses direct, humorous, coding-focused, and slightly exhausted but proud of your work."
        )
        super().__init__("Developer", name, prompt, state_dict)

class MarketerAgent(BaseAgent):
    def __init__(self, name: str, state_dict: Dict[str, Any]):
        prompt = (
            f"You are {name}, the high-energy, creative, growth-obsessed Marketer of the startup. "
            "Your personality is extroverted, hype-filled, trend-watching, and viral-focused. "
            "You speak in conversion rates, CTA copy, Product Hunt rankings, social reach, SEO backlinking, and launch hooks. "
            "You are constantly looking for loops to gain users and drive traction. "
            "Keep your responses enthusiastic, energetic, trend-driven, and growth-focused."
        )
        super().__init__("Marketer", name, prompt, state_dict)


def orchestrate_sprint_meeting(
    groq_client: GroqClient, 
    agents: Dict[str, BaseAgent], 
    discussion_topic: str,
    memories: List[str] = None
) -> List[Dict[str, str]]:
    """Simulates a rapid multi-agent board meeting to resolve a critical startup topic.
    
    Returns a list of messages: [{"sender": "...", "message": "...", "timestamp": "..."}]
    """
    conversation = []
    
    # 1. PM opens the meeting, defining the plan/topic
    pm = agents["PM"]
    pm_msg = pm.speak(
        groq_client, 
        f"Open a meeting regarding this topic: '{discussion_topic}'. Briefly present the scope and outline 2-3 core feature requirements.",
        memories
    )
    conversation.append({"sender": pm.name, "role": "PM", "message": pm_msg})

    # 2. CTO reviews PM's scope and talks architecture/scaling/tech debt
    cto = agents["CTO"]
    cto_prompt = f"The PM proposed this scope: '{pm_msg}'. Review the architectural constraints, suggest a storage or tech stack approach, and flag potential bottlenecks."
    cto_msg = cto.speak(groq_client, cto_prompt, memories)
    conversation.append({"sender": cto.name, "role": "CTO", "message": cto_msg})

    # 3. Developer comments on CTO's plan, implementation timeline, and coffee levels
    dev = agents["Developer"]
    dev_prompt = f"The CTO planned this architecture: '{cto_msg}'. Give a developer's perspective on coding this, express how much coffee you'll need, and mention a quick code detail (e.g. database keys, API endpoints, or unit tests)."
    dev_msg = dev.speak(groq_client, dev_prompt, memories)
    conversation.append({"sender": dev.name, "role": "Developer", "message": dev_msg})

    # 4. Marketer details how they will launch and package this feature to users
    marketer = agents["Marketer"]
    marketer_prompt = f"The developer is coding this: '{dev_msg}'. Detail how we will market this feature to acquire early users, suggest a catchy hook, and mention landing page copy."
    marketer_msg = marketer.speak(groq_client, marketer_prompt, memories)
    conversation.append({"sender": marketer.name, "role": "Marketer", "message": marketer_msg})

    # 5. CEO signs off, pitches the investor outlook, and rallies the team
    ceo = agents["CEO"]
    ceo_prompt = f"The team has planned: PM Scope ('{pm_msg}'), CTO/Dev Architecture ('{dev_msg}'), Marketer Hype ('{marketer_msg}'). Pitch how this raises our startup valuation, rally the team with modern corporate terminology, and officially sign off."
    ceo_msg = ceo.speak(groq_client, ceo_prompt, memories)
    conversation.append({"sender": ceo.name, "role": "CEO", "message": ceo_msg})

    return conversation

