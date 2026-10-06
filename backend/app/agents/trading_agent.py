from app.agents.base_agent import BaseAgent


class TradingAgent(BaseAgent):

    def __init__(self):

        super().__init__(
            name="Trading Agent",
            description=(
                "Handles trading analysis, trading journals, "
                "risk management, trading performance, "
                "support and resistance, and trading discipline."
            ),
            expertise=(
                "Support and Resistance strategy, multi-timeframe "
                "market structure, price action confirmation, "
                "trade planning, risk management, trading psychology, "
                "trading journals, performance analysis, "
                "and trading discipline."
            ),
            memory_category="trading"
        )

    def can_handle(self, request: str) -> bool:

        keywords = [
            "trading",
            "trade",
            "forex",
            "market structure",
            "support and resistance",
            "support & resistance",
            "s&r",
            "pullback",
            "risk management",
            "trading journal",
            "prop firm",
            "prop-firm",
            "propfirm",
            "entry",
            "stop loss",
            "take profit",
            "trading lesson",
            "trading mistake",
            "trading mistakes",
            "overleveraging",
            "overleveraged"
        ]

        request = request.lower()

        return any(
            keyword in request
            for keyword in keywords
        )


trading_agent = TradingAgent()
