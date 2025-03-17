graph_old: dict[str, list[str]] = {
    'Preprocessor': ['Analyzer1', 'Analyzer2'],
    'Analyzer1': ['Transformer'],
    'Analyzer2': ['Transformer'],
    'Transformer': ['Formatter'],
    'Formatter': ['Aggregator'],
    'Init': ['CacheManager', 'Logger'],
    'CacheManager': ['Aggregator'],
    'Logger': ['Aggregator'],
    'Aggregator': []
}



graph_new: dict[str, dict[str, list[str]]] = {
    'Preprocessor': {'next': ['Analyzer1', 'Analyzer2']},
    'Analyzer1': {'next': ['Transformer']},
    'Analyzer2': {'next': ['Transformer']},
    'Transformer': {'next': ['Formatter']},
    'Formatter': {'next': ['Aggregator']},
    'Init': {'next': ['CacheManager', 'Logger']},
    'CacheManager': {'next': ['Aggregator']},
    'Logger': {'next': ['Aggregator']},
    'Aggregator': {'next': []}
}

