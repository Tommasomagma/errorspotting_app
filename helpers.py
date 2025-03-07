
def GBLite2(string):

    opsLs = ['+', '-', '*', 'frac', 'cdot', 'times', '=']

    # Check if string contains at least two separate digits
    digit_count = 0
    prev_was_digit = False
    for c in string:
        if c.isdigit():
            if not prev_was_digit:
                digit_count += 1
            prev_was_digit = True
        else:
            prev_was_digit = False
    
    # Check if any operator from opsLs appears in the string
    operator_count = sum(string.count(op) for op in opsLs)

    if operator_count >= 2 and digit_count >= 3:
        return True
    else:
        return False