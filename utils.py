def print_separator(n = 100, character="-"):
    print(character * n)

def print_separators_bounded(string : str, n : int = 100, character : str ="-"):
    print_separator(n, character)
    print(string)
    print_separator(n, character)

def get_integer_input(prompt : str, acceptable_inputs : list[int]) -> int:
    while True:
        try:
            int_input = int(input(prompt))
        except:
            print("Invalid Input! Try Again")
            continue
        if int_input == -1:
            raise IndexError("Intentional Way to Break the Loop!")
        elif int_input not in acceptable_inputs:
            print(f"Invalid Input! Acceptable Inputs can be one of the following: {acceptable_inputs}")
            continue
        return int_input
