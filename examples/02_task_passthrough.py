"""
Example 2: Task Passthrough

Demonstrates why task_pass_through is essential:
- Each task carries independent data through the workflow
- on_complete callback is disconnected from where tasks are submitted
- task_pass_through enables accessing original task data in distant code
- Critical for batch processing where results are handled separately
"""

from flow4ai.flowmanager import FlowManager
from flow4ai.dsl import job


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


# This callback is defined SEPARATELY from where tasks are submitted
# It demonstrates how task_pass_through bridges disconnected code sections
def handle_completed_order(result):
    """
    Process completed orders - this runs in a DIFFERENT context from task submission.
    
    This callback has NO direct access to the original task data that was submitted.
    The only way to correlate results with specific orders is via task_pass_through.
    """
    # Access the ORIGINAL task data via task_pass_through
    # Without this, we wouldn't know which customer this result belongs to!
    task_data = result["task_pass_through"]
    
    # The result contains the processing output
    processing_result = result
    
    # Now we can correlate: "This processed order belongs to Customer Alice"
    order_id = task_data.get('process.order_id', 'UNKNOWN')
    customer = task_data.get('process.customer_name', 'UNKNOWN')
    
    print(f"📦 Order {order_id} completed for {customer}:")
    print(f"   Subtotal: ${processing_result['subtotal']:.2f}")
    print(f"   Tax: ${processing_result['tax']:.2f}")
    print(f"   Total: ${processing_result['total']:.2f}")
    print(f"   Status: {processing_result['status']}")
    print()


def main():
    """Run the task passthrough example."""
    print("\n" + "="*60)
    print("Example 2: Task Passthrough")
    print("="*60 + "\n")
    
    print("This example shows why task_pass_through is essential:\n")
    print("1. Tasks are submitted in main() with customer-specific data")
    print("2. Results are processed in handle_completed_order() callback")
    print("3. These are DISCONNECTED - callback has no access to submission context")
    print("4. task_pass_through is the ONLY way to correlate results with customers\n")
    
    # Wrap the function as a job
    dsl = job(process=process_order)
    
    # Create FlowManager with on_complete callback
    # NOTE: The callback is defined ABOVE, completely separate from this code
    fm = FlowManager(on_complete=handle_completed_order)
    fq_name = fm.add_dsl(dsl, "order_processor")
    
    # Submit multiple tasks with different customer data
    print("Processing multiple orders...\n")
    orders = [
        {"process.order_id": "ORD-001", "process.customer_name": "Alice", "process.amount": 100.00},
        {"process.order_id": "ORD-002", "process.customer_name": "Bob", "process.amount": 250.50},
        {"process.order_id": "ORD-003", "process.customer_name": "Charlie", "process.amount": 75.25},
    ]
    
    for order in orders:
        fm.submit_task(order, fq_name)
    
    # Wait for all tasks to complete
    # The on_complete callback will be invoked for each completed task
    success = fm.wait_for_completion()
    
    if not success:
        print("❌ Timeout waiting for tasks to complete")
        return False
    
    print("\n" + "="*60)
    print("Why task_pass_through matters:")
    print("="*60)
    print("✓ Submission code and callback are DISCONNECTED")
    print("✓ Callback has NO direct access to original task data")
    print("✓ task_pass_through is the ONLY bridge between them")
    print("✓ Essential for: batch processing, async workflows, distributed systems")
    print("✓ Without it: impossible to correlate 'Order ORD-001' with 'Alice'")
    print("="*60 + "\n")
    
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
