import os
import random
from dotenv import load_dotenv

# Try importing the official Groq library
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

load_dotenv()

# Pre-canned agent response templates for fallback/offline mode
MOCK_PATTERNS = {
    "CEO": [
        "Let's align our core deliverables with user traction. Scaling this strategy yields maximum ROI.",
        "We need to capture early adopters. A high-leverage launch will pivot our valuation toward the series A benchmark.",
        "Excellent synergy. Let's greenlight this road map, but remember, lean execution is our north star right now.",
        "That's a visionary approach. Let's make sure our narrative highlights the disruptive potential here."
    ],
    "CTO": [
        "From an architectural standpoint, we need to containerize the services and optimize query latency.",
        "We should be careful with technical debt here. A lightweight serverless API reduces hosting costs and deployment times.",
        "I'll set up a robust CI/CD pipeline and integrate error monitoring. Our current uptime metrics look positive.",
        "The codebase needs a minor refactor before we scale. Let's prioritize schema normalization first."
    ],
    "PM": [
        "I'll break this milestone down into actionable user stories and populate the sprint backlog.",
        "We need to balance development speed with code health to hit our MVP release deadline next week.",
        "Let's focus on the critical path. Unlocking the core payment workflow is our highest priority item.",
        "I've mapped out the user journey. Let's review these milestones to see if we can compress our schedule."
    ],
    "Developer": [
        "I'm refactoring the primary endpoints and squashing those database latency bugs. Coffee tank is filled.",
        "Working on the authentication modules. Found a few race conditions, but they're patched now.",
        "The feature is ready in staging! Tests are passing. Code coverage is currently at 86%.",
        "Just pushed a hotfix for the session leak. Let's deploy to production once the tests clear."
    ],
    "Marketer": [
        "I'm scripting viral outreach templates and designing high-conversion landing page layouts.",
        "Our Product Hunt launch strategy is set! We'll use cross-promotions and newsletter syndicates to boost traction.",
        "Conversion rates rose by 14% after we tweaked the CTA copy. Let's run a second A/B split test.",
        "I'm optimizing our SEO keywords and drafting a medium article to drive organic developer interest."
    ]
}

class GroqClient:
    """Manages queries to the Groq LPU API, with standard mock fallback capability."""

    def __init__(self):
        self.api_key = os.environ.get("GROQ_API_KEY")
        self.client = None
        self.is_connected = False

        if GROQ_AVAILABLE and self.api_key and "your_groq_api" not in self.api_key.lower():
            try:
                self.client = Groq(api_key=self.api_key)
                self.is_connected = True
            except Exception as e:
                print(f"Failed to initialize Groq client: {e}")

    def query(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        model: str = "llama-3.3-70b-versatile",
        temperature: float = 0.7,
        max_tokens: int = 1500
    ) -> str:

        if self.is_connected and self.client:
            try:
                chat_completion = self.client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return chat_completion.choices[0].message.content.strip()
            except Exception as e:
                # If API call fails, log error and drop down to mock generation
                print(f"Groq API Error: {e}. Falling back to simulation synthesis.")
        
        # Simulated intelligent generation based on sender identity
        return self._generate_simulated_response(system_prompt, user_prompt)

    def _generate_simulated_response(self, system_prompt: str, user_prompt: str) -> str:
        """Procedurally synthesizes logical fallback dialogue using context clues."""
        # Find which agent role is generating this
        sender_role = "System"
        for role in ["CEO", "CTO", "PM", "Developer", "Marketer"]:
            if role in system_prompt or role in user_prompt:
                sender_role = role
                break
        
        # Standard responses for various roles
        if sender_role in MOCK_PATTERNS:
            base = random.choice(MOCK_PATTERNS[sender_role])
        else:
            base = "Engaging agent simulator protocol. Optimizing system operations..."

        # Enrich based on inputs to simulate responsiveness
        if "valuation" in user_prompt.lower() or "money" in user_prompt.lower():
            if sender_role == "CEO":
                base += " Our current capitalization is solid, but securing a higher valuation requires steady growth metrics."
            elif sender_role == "CTO":
                base += " Let's make sure our tech cost projections remain optimal to protect our runway."
        elif "bug" in user_prompt.lower() or "crash" in user_prompt.lower():
            if sender_role == "Developer":
                base += " Pushing hotfixes immediately. Squash mode activated!"
            elif sender_role == "CTO":
                base += " Code stability is paramount. We should halt new features until we recover test parity."
        elif "launch" in user_prompt.lower() or "marketing" in user_prompt.lower() or "campaign" in user_prompt.lower():
            if sender_role == "Marketer":
                base += " Let's triple down on cold campaigns and developer community outreach!"
            elif sender_role == "PM":
                base += " Let's compile the launch checklist and make sure the MVP release is scoped correctly."

        return base
