import yaml

yaml_data = """
four_stage_parameterized: 
    params1:
        ask_llm:
          - model: "gpt-4o"
        read_file:
          - filepath: "./file1.txt"
        save_to_db:
          - database_url: "postgres://user1:pass1@db1/mydb"
            table_name: "table_a"
    params2:
        ask_llm:
          - model: "gpt-4o-mini"
        read_file:
          - filepath: "./file2.txt"
        save_to_db:
          - database_url: "sqlite://user2:pass2@db2/mydb"
            table_name: "table_b"

three_stage:
    params1:
        ask_llm_mini:
          - model: "gpt-4o-mini"
"""

data = yaml.safe_load(yaml_data)

# --- Level 1: The outermost dictionaries ---

print("Level 1: data.items()")
for key, value in data.items():
    print(f"  Key: {key}, \nValue: {value}")
print()
print("Level 1: data.keys()")
print(data.keys())
print()
# --- Level 2:  Accessing 'four_stage_parameterized' dict and its items ---
four_stage_params = data['four_stage_parameterized']
print("Level 2: four_stage_params.items()")
for key, value in four_stage_params.items():
    print(f"  Key: {key}, \nValue: {value}")
print()
print("Level 2: four_stage_params.keys()")  
print(four_stage_params.keys())
print()

# --- Level 3: Accessing 'params1' inside 'four_stage_parameterized'  ---

params1 = four_stage_params['params1']
print("Level 3: params1.items()")
for key, value in params1.items():
    print(f"  Key: {key}, \nValue: {value}")
print()
print("Level 3: params1.keys()")
print(params1.keys())
print()
# --- Level 4: Accessing the inner dict for 'ask_llm' inside 'params1' (it contains a list) ---
ask_llm = params1['ask_llm']
print("Level 4: ask_llm (list). This is a list, not a dict.  Accessing the first element (a dict) directly.")
print(ask_llm)
first_ask_llm_item = ask_llm[0]
print("Level 4b: first_ask_llm_item.items()")
for key, value in first_ask_llm_item.items():
    print(f"  Key: {key}, \nValue: {value}")
print()

# --- Example using 'three_stage' ---

three_stage = data['three_stage']
params1_three_stage = three_stage['params1']
print("Three stage params1 dict:")
for key, value in params1_three_stage.items():
    print(f"  Key: {key}, \nValue: {value}")
print()

# --- Example getting to model from three_stage
ask_llm_mini = params1_three_stage['ask_llm_mini']
print("Three stage ask_llm_mini list:")
print(ask_llm_mini)
ask_llm_mini_dict = ask_llm_mini[0]
print("Three stage ask_llm_mini dict:")
for key, value in ask_llm_mini_dict.items():
    print(f"  Key: {key}, \nValue: {value}")
print()


# --- Example of iterating save_to_db list of dictionaries
params2 = data['four_stage_parameterized']['params2']
save_to_db_list = params2['save_to_db']
print("Iterating the save_to_db_list:")
for save_to_db_dict in save_to_db_list:
    print("  save_to_db_dict:")
    for key, value in save_to_db_dict.items():
        print(f"    Key: {key}, \nValue: {value}")

