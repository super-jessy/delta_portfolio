from .trendline_tool import TrendlineTool

class DrawingToolFactory:
    @staticmethod
    def create(tool_name, chart):
        if tool_name == "Trendline":
            return TrendlineTool(chart)
        return None
