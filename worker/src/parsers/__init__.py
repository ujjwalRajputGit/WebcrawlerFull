from .simple_parser import SimpleParser
# from .ai_parser_old import AIParser
from .ai_parser_langchain import AIParser
from .config_parser import ConfigParser
from constants import ParserType
__all__ = ["ai_parser_langchain", "config_parser", "simple_parser"]

    # Optimized parser selection using dictionary mapping
PARSERS = {
    ParserType.SIMPLE: SimpleParser,
    ParserType.AI: AIParser,
    ParserType.CONFIG: ConfigParser,
}

def get_parser(parser_type: ParserType):
    """
    Returns the appropriate parser instance.
    """
    parser_class = PARSERS.get(parser_type)
    if not parser_class:
        raise ValueError(f"Unknown parser type: {parser_type}")
    return parser_class()


# # Parser selection logic
# def get_parser(parser_type: ParserType):
#     """
#     Returns the appropriate parser based on the given type.
    
#     Args:
#         parser_type (ParserType): The type of parser (ParserType.SIMPLE, ParserType.AI, ParserType.CONFIG)

#     Returns:
#         Object: Instance of the requested parser class.
#     """
#     if parser_type == ParserType.SIMPLE:
#         return SimpleParser()
#     elif parser_type == ParserType.AI:
#         return ValueError("AI Parser is not implemented yet.")
#     elif parser_type == ParserType.CONFIG:
#         return ConfigParser()
#     else:
#         raise ValueError(f"Unknown parser type: {parser_type}")
