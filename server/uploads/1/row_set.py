class RowSet:
    def __init__(self, codes={}, prime=8191):
        self.codes = {
            'a': 1,
            'b': 2,
            'c': 3,
            'd': 4,
            'e': 5,
            'f': 6,
            'g': 7,
            'h': 8,
            'i': 9,
            'j': 10,
            'k': 11,
            'l': 12,
            'm': 13,
            'n': 14,
            'o': 15,
            'p': 16,
            'q': 17,
            'r': 18,
            's': 19,
            't': 20,
            'u': 21,
            'v': 22,
            'w': 23,
            'x': 24,
            'y': 25,
            'z': 26
}
        self.prime = prime
        self.list_of_rows = []
        self.pow_of_ten = [1, 10, 100, 1000, 1809, 1708, 698, 6980, 4272, 1765, 1268, 4489, 3935, 6586, 332]
        with open("input.txt", "r") as input_file_object:
            all_lines = input_file_object.readlines()
        for line in all_lines:
            operator = line[0]
            operand = line[2:]
            if operator == '+':
                self.list_of_rows.append(operand)
            elif operator == '-':
                try:
                    self.list_of_rows.remove(operand)
                except:
                    pass
            elif operator == '?':
                with open("output.txt", "a") as output_file_object:
                    output_file_object.write(self.is_contains(operand) + '\n')
            else:
                pass

    def polynomial_hash(self, string): # m
        result = 0 # 1
        iterator = 0 # 1
        for letter in string: # m
            if letter != '\n': # 1
                result += (self.pow_of_ten[iterator] * (self.codes[letter] % self.prime)) % self.prime # 1
                iterator += 1 # 1
        return result % self.prime # 1

    def is_contains(self, string):
        hash1 = self.polynomial_hash(string)
        for row in self.list_of_rows:
            hash2 = self.polynomial_hash(row)
            if hash1 == hash2:
                return "yes"
        return "no"

    def find_palindromes(self): # nm
        for string in self.list_of_rows: # n
            if self.is_palindrome(string): # m
                print(string) # 1

    def is_palindrome(self, string): # m
        half_length = (len(string) - 1) // 2 # m
        if (len(string) - 1) % 2 == 0: # m
            first_half = string[:half_length] # m
            second_half = "".join(reversed(string[half_length:])) # m
        else:
            first_half = string[:half_length] # m
            second_half = "".join(reversed(string[half_length+1:])) # m
        if self.polynomial_hash(first_half) == self.polynomial_hash(second_half): # 2m
            return True
        return False
