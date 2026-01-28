"""
Example 2: Task Passthrough

Demonstrates why task_pass_through is essential:
- Each task carries independent data through the workflow
- Results need access to original task data for processing
- Shows how to retrieve task-specific information from results
"""

from flow4ai.flowmanager import FlowManager
from flow4ai.dsl import wrap


def process_order(order_id, customer_name, amount):
    """Process a customer order."""
    tax_rate = 0.08
    tax = amount * tax_rate
    total = amount + tax
    
    return {
        "subtotal": amount,
        "tax": tax,
        "total": total,
        "status": "processed"
    }


def main():
    """Run the task passthrough example."""
    print("\n" + "="*60)
    print("Example 2: Task Passthrough")
    print("="*60 + "\n")
    
    print("Processing multiple orders with different customer data...\n")
    
    # Wrap the function as a job
    jobs = wrap({"process": process_order})
    dsl = jobs["process"]
    
    # Create FlowManager instance
    fm = FlowManager()
    fq_name = fm.add_dsl(dsl, "order_processor")
    
    # Submit multiple tasks with different customer data
    orders = [
        {"process.order_id": "ORD-001", "process.customer_name": "Alice", "process.amount": 100.00},
        {"process.order_id": "ORD-002", "process.customer_name": "Bob", "process.amount": 250.50},
        {"process.order_id": "ORD-003", "process.customer_name": "Charlie", "process.amount": 75.25},
    ]
    
    for order in orders:
        fm.submit_task(order, fq_name)
    
    # Wait for all tasks to complete
    success = fm.wait_for_completion()
    
    if not success:
        print("❌ Timeout waiting for tasks to complete")
        return False
    
    # Get results
    results = fm.pop_results()
    
    if results["errors"]:
        print(f"❌ Errors occurred: {results['errors']}")
        return False
    
    print("✅ All orders processed!\n")
    print("Results (with task_pass_through):\n")
    
    # Extract completed results
    completed_results = list(results["completed"].values())[0]
    
    for result in completed_results:
        # Access the ORIGINAL task data via task_pass_through
        task_data = result["task_pass_through"]
        
        # The result itself contains the processing output
        processing_result = result["result"]
        
        print(f"Order ID: {task_data.get('process.order_id', 'N/A')}")
        print(f"  Customer: {task_data.get('process.customer_name', 'N/A')}")
        print(f"  Subtotal: ${processing_result['subtotal']:.2f}")
        print(f"  Tax: ${processing_result['tax']:.2f}")
        print(f"  Total: ${processing_result['total']:.2f}")
        print(f"  Status: {processing_result['status']}")
        print()
    
    print("Why task_pass_through matters:")
    print("  - Each task has INDEPENDENT data (different customers, amounts)")
    print("  - Processing functions see only their parameters")
    print("  - task_pass_through preserves ORIGINAL task data in results")
    print("  - Essential for batch processing and result correlation")
    
    print("\n" + "="*60 + "\n")
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
