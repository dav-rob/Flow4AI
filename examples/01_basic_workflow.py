"""
Example 1: Basic Workflow

Demonstrates the core Flow4AI concepts:
- Defining jobs as simple functions
- Building workflows with serial (>>) and parallel (|) operators
- Executing tasks and retrieving results
"""

from flow4ai.flowmanager import FlowManager
from flow4ai.dsl import wrap, p


def analyze_text(text):
    """Extract key information from text."""
    words = text.split()
    return {
        "word_count": len(words),
        "first_word": words[0] if words else "",
        "last_word": words[-1] if words else ""
    }


def check_sentiment(text):
    """Perform simple sentiment analysis."""
    positive_words = {"good", "great", "excellent", "awesome", "fantastic"}
    negative_words = {"bad", "terrible", "awful", "poor", "horrible"}
    
    words = set(text.lower().split())
    positive_count = len(words & positive_words)
    negative_count = len(words & negative_words)
    
    if positive_count > negative_count:
        sentiment = "positive"
    elif negative_count > positive_count:
        sentiment = "negative"
    else:
        sentiment = "neutral"
    
    return {"sentiment": sentiment, "positive_count": positive_count, "negative_count": negative_count}


def extract_keywords(text):
    """Extract potential keywords from text."""
    # Simple keyword extraction: words longer than 4 characters
    words = text.split()
    keywords = [w for w in words if len(w) > 4]
    return {"keywords": keywords, "keyword_count": len(keywords)}


def aggregate_analysis(j_ctx):
    """Combine results from all analysis branches."""
    inputs = j_ctx["inputs"]
    
    # Get results from each parallel analysis job
    text_analysis = inputs.get("analyze", {})
    sentiment = inputs.get("sentiment", {})
    keywords = inputs.get("keywords", {})
    
    return {
        "summary": {
            "word_count": text_analysis.get("word_count", 0),
            "sentiment": sentiment.get("sentiment", "unknown"),
            "top_keywords": keywords.get("keywords", [])[:3],
        }
    }


def main():
    """Run the basic workflow example."""
    print("\n" + "="*60)
    print("Example 1: Basic Workflow")
    print("="*60 + "\n")
    
    # Create jobs from our functions
    jobs = wrap({
        "analyze": analyze_text,
        "sentiment": check_sentiment,
        "keywords": extract_keywords,
        "aggregate": aggregate_analysis
    })
    
    # Save intermediate results so aggregate can access them
    jobs["analyze"].save_result = True
    jobs["sentiment"].save_result = True
    jobs["keywords"].save_result = True
    
    # Build workflow: 3 parallel analysis jobs >> aggregation
    # p() creates parallel branches that execute concurrently
    dsl = p(jobs["analyze"], jobs["sentiment"], jobs["keywords"]) >> jobs["aggregate"]
    
    # Execute the workflow
    task = {
        "analyze.text": "This is a great example of text analysis",
        "sentiment.text": "This is a great example of text analysis",
        "keywords.text": "This is a great example of text analysis"
    }
    
    print("Input text: 'This is a great example of text analysis'\n")
    print("Running parallel analysis (analyze + sentiment + keywords) >> aggregate...\n")
    
    errors, result = FlowManager.run(dsl, task, graph_name="text_analyzer")
    
    if errors:
        print(f"❌ Errors occurred: {errors}")
        return False
    
    print("✅ Analysis complete!\n")
    print("Results:")
    print(f"  - Word Count: {result['summary']['word_count']}")
    print(f"  - Sentiment: {result['summary']['sentiment']}")
    print(f"  - Top Keywords: {', '.join(result['summary']['top_keywords'])}")
    
    print("\nNote: This example uses FlowManager.run() which returns errors and the final result.")
    print("For batch processing, use FlowManager() instance with submit_task() and pop_results().")
    
    print("\n" + "="*60 + "\n")
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
