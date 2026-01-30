"""
Tests for job data access patterns: get_inputs() and get_saved_results().

Tests verify that:
1. get_inputs() returns only immediate predecessors' outputs
2. get_saved_results() / j_ctx["saved_results"] returns all saved results from earlier jobs
3. Both JobABC classes and wrapped functions have consistent access
"""

import pytest
from flow4ai.flowmanager import FlowManager
from flow4ai.dsl import job
from flow4ai.job import JobABC


# =============================================================================
# Test Fixtures - Job Classes
# =============================================================================

class JobA(JobABC):
    """First job in chain - returns initial data."""
    def __init__(self):
        super().__init__('job_a')
    
    async def run(self, task):
        return {'a_value': 100, 'a_name': 'from_a'}


class JobB(JobABC):
    """Second job - verifies it can see job_a in inputs."""
    def __init__(self):
        super().__init__('job_b')
        self.received_inputs = {}
    
    async def run(self, task):
        self.received_inputs = self.get_inputs()
        a_data = self.received_inputs.get('job_a', {})
        return {'b_value': 200, 'a_value_received': a_data.get('a_value', 'NOT_FOUND')}


class JobC(JobABC):
    """Third job - verifies inputs vs saved_results access."""
    def __init__(self):
        super().__init__('job_c')
        self.received_inputs = {}
        self.received_saved = {}
    
    async def run(self, task):
        self.received_inputs = self.get_inputs()
        self.received_saved = self.get_saved_results()
        return {
            'c_result': 'done',
            'inputs_keys': list(self.received_inputs.keys()),
            'saved_keys': list(self.received_saved.keys()),
        }


# =============================================================================
# Test: JobABC class inputs only sees immediate predecessors
# =============================================================================

@pytest.mark.asyncio
async def test_jobabc_inputs_only_sees_immediate_predecessor():
    """JobABC.get_inputs() should only return immediate predecessors, not earlier jobs."""
    job_a = JobA()
    job_b = JobB()
    job_c = JobC()
    
    workflow = job_a >> job_b >> job_c
    
    errors, result = FlowManager.run(workflow, {}, 'test_inputs')
    
    assert not errors, f"Unexpected errors: {errors}"
    
    # job_c should only see job_b in inputs, NOT job_a
    assert 'job_b' in result['inputs_keys'], "job_c should see job_b in inputs"
    assert 'job_a' not in result['inputs_keys'], "job_c should NOT see job_a in inputs (only immediate predecessors)"


# =============================================================================
# Test: JobABC class saved_results sees earlier jobs (with save_result=True)
# =============================================================================

@pytest.mark.asyncio
async def test_jobabc_saved_results_sees_earlier_jobs():
    """JobABC.get_saved_results() should return results from jobs with save_result=True."""
    job_a = JobA()
    job_a.save_result = True  # Mark job_a to save its result
    
    job_b = JobB()
    job_c = JobC()
    
    workflow = job_a >> job_b >> job_c
    
    errors, result = FlowManager.run(workflow, {}, 'test_saved')
    
    assert not errors, f"Unexpected errors: {errors}"
    
    # job_c should see job_a in saved_results
    assert 'job_a' in result['saved_keys'], "job_c should see job_a in saved_results"
    
    # Verify the actual saved data is accessible
    assert job_c.received_saved.get('job_a', {}).get('a_value') == 100


# =============================================================================
# Test: Wrapped function j_ctx["inputs"] only sees immediate predecessors
# =============================================================================

@pytest.mark.asyncio
async def test_wrapped_function_inputs_only_sees_immediate_predecessor():
    """Wrapped functions' j_ctx['inputs'] should only return immediate predecessors."""
    
    received_by_fn_c = {}
    
    def fn_a():
        return {'a_value': 100}
    
    def fn_b(j_ctx):
        return {'b_value': 200}
    
    def fn_c(j_ctx):
        nonlocal received_by_fn_c
        received_by_fn_c = {
            'inputs_keys': list(j_ctx['inputs'].keys()),
            'saved_keys': list(j_ctx.get('saved_results', {}).keys()),
        }
        return {'c_result': 'done'}
    
    jobs = job({'fn_a': fn_a, 'fn_b': fn_b, 'fn_c': fn_c})
    workflow = jobs['fn_a'] >> jobs['fn_b'] >> jobs['fn_c']
    
    errors, result = FlowManager.run(workflow, {}, 'test_fn_inputs')
    
    assert not errors, f"Unexpected errors: {errors}"
    
    # fn_c should only see fn_b in inputs
    assert 'fn_b' in received_by_fn_c['inputs_keys'], "fn_c should see fn_b in inputs"
    assert 'fn_a' not in received_by_fn_c['inputs_keys'], "fn_c should NOT see fn_a in inputs"


# =============================================================================
# Test: Wrapped function j_ctx["saved_results"] sees earlier jobs
# =============================================================================

@pytest.mark.asyncio
async def test_wrapped_function_saved_results_sees_earlier_jobs():
    """Wrapped functions' j_ctx['saved_results'] should return results from saved jobs."""
    
    received_by_fn_c = {}
    
    def fn_a():
        return {'a_value': 100}
    
    def fn_b(j_ctx):
        return {'b_value': 200}
    
    def fn_c(j_ctx):
        nonlocal received_by_fn_c
        received_by_fn_c = {
            'inputs_keys': list(j_ctx['inputs'].keys()),
            'saved_keys': list(j_ctx.get('saved_results', {}).keys()),
            'a_value': j_ctx['saved_results'].get('fn_a', {}).get('a_value'),
        }
        return {'c_result': 'done'}
    
    jobs = job({'fn_a': fn_a, 'fn_b': fn_b, 'fn_c': fn_c})
    jobs['fn_a'].save_result = True  # Mark fn_a to save its result
    
    workflow = jobs['fn_a'] >> jobs['fn_b'] >> jobs['fn_c']
    
    errors, result = FlowManager.run(workflow, {}, 'test_fn_saved')
    
    assert not errors, f"Unexpected errors: {errors}"
    
    # fn_c should see fn_a in saved_results
    assert 'fn_a' in received_by_fn_c['saved_keys'], "fn_c should see fn_a in saved_results"
    assert received_by_fn_c['a_value'] == 100, "fn_c should access fn_a's a_value via saved_results"


# =============================================================================
# Test: Multiple jobs can have save_result=True
# =============================================================================

@pytest.mark.asyncio
async def test_multiple_jobs_with_save_result():
    """Multiple jobs can have save_result=True and all are accessible."""
    
    received_saved = {}
    
    def fn_a():
        return {'a_value': 100}
    
    def fn_b(j_ctx):
        return {'b_value': 200}
    
    def fn_c(j_ctx):
        return {'c_value': 300}
    
    def fn_d(j_ctx):
        nonlocal received_saved
        received_saved = j_ctx.get('saved_results', {})
        return {'d_result': 'done'}
    
    jobs = job({'fn_a': fn_a, 'fn_b': fn_b, 'fn_c': fn_c, 'fn_d': fn_d})
    jobs['fn_a'].save_result = True
    jobs['fn_b'].save_result = True
    # fn_c does NOT have save_result=True
    
    workflow = jobs['fn_a'] >> jobs['fn_b'] >> jobs['fn_c'] >> jobs['fn_d']
    
    errors, result = FlowManager.run(workflow, {}, 'test_multi_saved')
    
    assert not errors, f"Unexpected errors: {errors}"
    
    # fn_d should see both fn_a and fn_b in saved_results, but NOT fn_c
    assert 'fn_a' in received_saved, "fn_d should see fn_a in saved_results"
    assert 'fn_b' in received_saved, "fn_d should see fn_b in saved_results"
    assert 'fn_c' not in received_saved, "fn_d should NOT see fn_c (save_result=False)"
    
    # Verify actual values
    assert received_saved['fn_a']['a_value'] == 100
    assert received_saved['fn_b']['b_value'] == 200
