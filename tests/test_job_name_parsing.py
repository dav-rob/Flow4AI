import pytest

from flow4ai.job import JobABC


def test_parse_graph_name():
    # Valid cases
    assert JobABC.parse_graph_name("four_stage_parameterized$$params1$$read_file$$") == "four_stage_parameterized"
    assert JobABC.parse_graph_name("three_stage_reasoning$$$$ask_llm_reasoning$$") == "three_stage_reasoning"
    
    # Invalid cases
    assert JobABC.parse_graph_name("invalid_name") == "UNSUPPORTED NAME FORMAT"
    assert JobABC.parse_graph_name("$$$$$$") == "UNSUPPORTED NAME FORMAT"
    assert JobABC.parse_graph_name("name$$param$$job") == "UNSUPPORTED NAME FORMAT"
    assert JobABC.parse_graph_name("") == "UNSUPPORTED NAME FORMAT"

def test_parse_param_name():
    # Valid cases
    assert JobABC.parse_param_name("four_stage_parameterized$$params1$$read_file$$") == "params1"
    assert JobABC.parse_param_name("three_stage_reasoning$$$$ask_llm_reasoning$$") == ""
    
    # Invalid cases
    assert JobABC.parse_param_name("invalid_name") == "UNSUPPORTED NAME FORMAT"
    assert JobABC.parse_param_name("$$$$$$") == "UNSUPPORTED NAME FORMAT"
    assert JobABC.parse_param_name("name$$param$$job") == "UNSUPPORTED NAME FORMAT"
    assert JobABC.parse_param_name("") == "UNSUPPORTED NAME FORMAT"

def test_parse_job_name():
    # Valid cases
    assert JobABC.parse_job_name("four_stage_parameterized$$params1$$read_file$$") == "read_file"
    assert JobABC.parse_job_name("three_stage_reasoning$$$$ask_llm_reasoning$$") == "ask_llm_reasoning"
    
    # Invalid cases
    assert JobABC.parse_job_name("invalid_name") == "UNSUPPORTED NAME FORMAT"
    assert JobABC.parse_job_name("$$$$$$") == "UNSUPPORTED NAME FORMAT"
    assert JobABC.parse_job_name("name$$param$$job") == "UNSUPPORTED NAME FORMAT"
    assert JobABC.parse_job_name("") == "UNSUPPORTED NAME FORMAT"

def test_parse_job_loader_name():
    # Valid cases with parameters
    result1 = JobABC.parse_job_loader_name("four_stage_parameterized$$params1$$read_file$$")
    assert result1 == {
        "graph_name": "four_stage_parameterized",
        "param_name": "params1",
        "job_name": "read_file"
    }
    
    # Valid cases without parameters
    result2 = JobABC.parse_job_loader_name("three_stage_reasoning$$$$ask_llm_reasoning$$")
    assert result2 == {
        "graph_name": "three_stage_reasoning",
        "param_name": "",
        "job_name": "ask_llm_reasoning"
    }
    
    # Invalid cases
    invalid_cases = [
        "invalid_name",
        "$$$$$$",
        "name$$param$$job",
        "",
        "name$$param$$job$$extra$$",
        "name$$param$$job$"
    ]
    
    for invalid_case in invalid_cases:
        result = JobABC.parse_job_loader_name(invalid_case)
        assert result == {"parsing_message": "UNSUPPORTED NAME FORMAT"}, f"Failed for case: {invalid_case}"

def test_get_input_from():
    # Create mock input data with realistic job names
    mock_inputs = {
        'four_stage_parameterized$$params1$$read_file$$': {'file_content': 'data1'},
        'four_stage_parameterized$$params1$$ask_llm$$': {'llm_response': 'answer1'},
        'four_stage_parameterized$$params1$$save_to_db$$': {'db_status': 'saved'},
        'four_stage_parameterized$$params1$$summarize$$': {'summary': 'text1'},
        'three_stage$$params1$$ask_llm_mini$$': {'mini_response': 'short_answer'},
        'three_stage_reasoning$$$$ask_llm_reasoning$$': {'reasoning': 'explanation'}
    }

    # Test getting input by short job name
    assert JobABC.get_input_from(mock_inputs, 'read_file') == {'file_content': 'data1'}
    assert JobABC.get_input_from(mock_inputs, 'ask_llm') == {'llm_response': 'answer1'}
    assert JobABC.get_input_from(mock_inputs, 'save_to_db') == {'db_status': 'saved'}
    assert JobABC.get_input_from(mock_inputs, 'summarize') == {'summary': 'text1'}
    assert JobABC.get_input_from(mock_inputs, 'ask_llm_mini') == {'mini_response': 'short_answer'}
    assert JobABC.get_input_from(mock_inputs, 'ask_llm_reasoning') == {'reasoning': 'explanation'}

    # Test non-existent job name returns empty dict
    assert JobABC.get_input_from(mock_inputs, 'non_existent_job') == {}

    # Test with empty inputs dict
    assert JobABC.get_input_from({}, 'read_file') == {}

    # Test that we get the first matching job when multiple jobs have same short name
    # In this case, read_file appears in both params1 and params2
    assert JobABC.get_input_from(mock_inputs, 'read_file') == {'file_content': 'data1'}
