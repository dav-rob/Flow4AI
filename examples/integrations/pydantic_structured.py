"""
Pydantic Structured Extraction

Demonstrates extracting structured data from unstructured text using
Pydantic models with Flow4AI parallel execution:
- Define Pydantic schemas for structured output
- Use LangChain's .with_structured_output() for type-safe extraction
- Run multiple extractions in parallel with Flow4AI

Prerequisites:
    pip install -e ".[test]"  # Installs langchain-core, langchain-openai, pydantic
    export OPENAI_API_KEY=your_key_here
"""

import asyncio
import os
from typing import List, Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from flow4ai.flowmanager import FlowManager
from flow4ai.dsl import job, p

# Load environment variables from .env file
load_dotenv()

try:
    from langchain_openai import ChatOpenAI
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    print("⚠️  LangChain not installed. Install with: pip install -e \".[test]\"")


# =============================================================================
# Pydantic Models - Define the structure of extracted data
# =============================================================================

class Product(BaseModel):
    """Structured representation of a product."""
    name: str = Field(description="The product name")
    price: float = Field(description="The price in USD")
    features: List[str] = Field(description="List of key features")
    brand: Optional[str] = Field(default=None, description="The brand name if mentioned")


# =============================================================================
# Sample Data - Embedded product descriptions
# =============================================================================

SAMPLE_TEXTS = [
    "iPhone 15 Pro - $999 - Features: A17 chip, titanium design, 48MP camera, USB-C port",
    "Samsung Galaxy S24 Ultra - $1199 - Features: AI features, 200MP camera, S-Pen included",
    "Google Pixel 8 - $699 - Features: Tensor G3 chip, 7 years updates, AI photo editing",
]


# =============================================================================
# Extraction Jobs - Async functions that extract structured data
# =============================================================================

async def extract_product(text: str) -> dict:
    """Extract structured product info from text using LangChain structured output."""
    if not LANGCHAIN_AVAILABLE:
        return {"error": "LangChain not installed"}
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, max_tokens=150)
    
    # Use LangChain's structured output feature
    structured_llm = llm.with_structured_output(Product)
    
    result = await structured_llm.ainvoke(
        f"Extract product information from this text: {text}"
    )
    
    # Convert Pydantic model to dict for Flow4AI result
    return {
        "product": result.model_dump(),
        "source_text": text[:50] + "..."
    }


async def aggregate_products(j_ctx) -> dict:
    """Aggregate all extracted products from parallel jobs.
    
    Uses j_ctx["inputs"] to access results from all upstream jobs.
    """
    inputs = j_ctx["inputs"]
    
    products = []
    for key in ["product1", "product2", "product3"]:
        result = inputs.get(key, {})
        if "product" in result:
            products.append(result["product"])
    
    return {"products": products, "count": len(products)}


# =============================================================================
# Main - Core Flow4AI + Pydantic integration
# =============================================================================

def main():
    """Run the Pydantic structured extraction example."""
    if not LANGCHAIN_AVAILABLE:
        print("\n❌ LangChain is not installed.")
        print("Install with: pip install -e \".[test]\"\n")
        return False
    
    _print_header()
    
    # Create extraction jobs - one for each product text
    jobs = job({
        "product1": extract_product,
        "product2": extract_product,
        "product3": extract_product,
        "aggregate": aggregate_products,
    })
    
    # Pattern: parallel extraction >> aggregation
    # All 3 extractions run concurrently, then aggregate collects results
    workflow = p(jobs["product1"], jobs["product2"], jobs["product3"]) >> jobs["aggregate"]
    
    # Task routes each text to its extraction job
    task = {
        "product1.text": SAMPLE_TEXTS[0],
        "product2.text": SAMPLE_TEXTS[1],
        "product3.text": SAMPLE_TEXTS[2],
    }
    
    # Execute the workflow
    errors, results = FlowManager.run(workflow, task, "pydantic_extraction", timeout=30)
    
    if errors:
        print(f"❌ Errors occurred: {errors}")
        return False
    
    _print_results(results)
    return True


# =============================================================================
# Output Helpers - Terminal display formatting
# =============================================================================

def _print_header():
    """Print example header and description."""
    print("\n" + "="*60)
    print("Pydantic Structured Extraction")
    print("="*60 + "\n")
    print("This example demonstrates:")
    print("- Pydantic models for structured LLM output")
    print("- LangChain's .with_structured_output() method")
    print("- Parallel extraction >> aggregation pattern\n")


def _print_results(results):
    """Print extracted products and observations."""
    print("="*60)
    print("✅ Extraction Complete")
    print("="*60 + "\n")
    
    products = results.get("products", [])
    for product in products:
        print(f"📦 {product.get('name', 'Unknown')}")
        print(f"   Brand: {product.get('brand', 'N/A')}")
        print(f"   Price: ${product.get('price', 0):.2f}")
        print(f"   Features: {', '.join(product.get('features', []))}")
        print()
    
    print("="*60)
    print("Key Observations:")
    print("="*60)
    print("✓ Pydantic validates and types all extracted fields")
    print("✓ All 3 extractions ran in parallel (not sequential)")
    print("✓ Aggregate job collected results via j_ctx['inputs']")
    print("✓ Results are type-safe Python objects")
    print("="*60 + "\n")


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
