import argparse
import xml.etree.ElementTree as ET

# Лексический анализатор (токенизатор)
class Lexer:
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.tokens = []

    def tokenize(self):
        while self.pos < len(self.text):
            if self.text[self.pos:self.pos+2] == '#=':
                self.pos += 2
                while self.text[self.pos:self.pos+2] != '=#':
                    self.pos += 1
                self.pos += 2
            elif self.text[self.pos].isspace():
                self.pos += 1
            elif self.text[self.pos].isdigit() or self.text[self.pos] == '.':
                start = self.pos
                while self.pos < len(self.text) and (self.text[self.pos].isdigit() or self.text[self.pos] == '.'):
                    self.pos += 1
                self.tokens.append(('NUMBER', self.text[start:self.pos]))
            elif self.text[self.pos].isalpha():
                start = self.pos
                while self.pos < len(self.text) and self.text[self.pos].isalpha():
                    self.pos += 1
                self.tokens.append(('IDENTIFIER', self.text[start:self.pos]))
            else:
                self.tokens.append((self.text[self.pos], self.text[self.pos]))
                self.pos += 1
        return self.tokens

# Синтаксический анализатор (парсер)
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.variables = {}

    def parse(self):
        self.parse_statements()
        return self.variables

    def parse_statements(self):
        while self.pos < len(self.tokens):
            if self.tokens[self.pos][0] == 'var':
                self.parse_variable_declaration()
            elif self.tokens[self.pos][0] == '{':
                self.parse_dictionary()
            else:
                raise SyntaxError(f"Unexpected token: {self.tokens[self.pos]}")

    def parse_variable_declaration(self):
        self.pos += 1
        if self.tokens[self.pos][0] != 'IDENTIFIER':
            raise SyntaxError("Expected identifier after 'var'")
        name = self.tokens[self.pos][1]
        self.pos += 1
        if self.tokens[self.pos][0] != '=':
            raise SyntaxError("Expected '=' after identifier")
        self.pos += 1
        value = self.parse_value()
        if self.tokens[self.pos][0] != ';':
            raise SyntaxError("Expected ';' after value")
        self.pos += 1
        self.variables[name] = value

    def parse_value(self):
        if self.tokens[self.pos][0] == 'NUMBER':
            return float(self.tokens[self.pos][1])
        elif self.tokens[self.pos][0] == 'IDENTIFIER':
            return self.variables[self.tokens[self.pos][1]]
        elif self.tokens[self.pos][0] == '@':
            return self.parse_postfix_expression()
        elif self.tokens[self.pos][0] == '{':
            return self.parse_dictionary()
        else:
            raise SyntaxError(f"Unexpected token: {self.tokens[self.pos]}")

    def parse_postfix_expression(self):
        self.pos += 2  # Skip '@['
        stack = []
        while self.tokens[self.pos][0] != ']':
            if self.tokens[self.pos][0] == 'IDENTIFIER':
                stack.append(self.variables[self.tokens[self.pos][1]])
            elif self.tokens[self.pos][0] == 'NUMBER':
                stack.append(float(self.tokens[self.pos][1]))
            elif self.tokens[self.pos][0] in '+-*/':
                b = stack.pop()
                a = stack.pop()
                if self.tokens[self.pos][0] == '+':
                    stack.append(a + b)
                elif self.tokens[self.pos][0] == '-':
                    stack.append(a - b)
                elif self.tokens[self.pos][0] == '*':
                    stack.append(a * b)
                elif self.tokens[self.pos][0] == '/':
                    stack.append(a / b)
            elif self.tokens[self.pos][0] == 'mod':
                b = stack.pop()
                a = stack.pop()
                stack.append(a % b)
            self.pos += 1
        self.pos += 1  # Skip ']'
        return stack[0]

    def parse_dictionary(self):
        self.pos += 1  # Skip '{'
        dictionary = {}
        while self.tokens[self.pos][0] != '}':
            if self.tokens[self.pos][0] != 'IDENTIFIER':
                raise SyntaxError("Expected identifier in dictionary")
            key = self.tokens[self.pos][1]
            self.pos += 1
            if self.tokens[self.pos][0] != ':':
                raise SyntaxError("Expected ':' after identifier in dictionary")
            self.pos += 1
            value = self.parse_value()
            dictionary[key] = value
            if self.tokens[self.pos][0] == ',':
                self.pos += 1
        self.pos += 1  # Skip '}'
        return dictionary

# Генератор XML
class XMLGenerator:
    def generate_xml(self, variables):
        root = ET.Element("config")
        self.add_dictionary(root, variables)
        return ET.tostring(root, encoding='unicode')

    def add_dictionary(self, parent, dictionary):
        dict_element = ET.SubElement(parent, "dictionary")
        for key, value in dictionary.items():
            entry_element = ET.SubElement(dict_element, "entry", name=key)
            if isinstance(value, dict):
                self.add_dictionary(entry_element, value)
            else:
                entry_element.set("value", str(value))

# Основная функция
def main():
    parser = argparse.ArgumentParser(description='Configuration Language to XML Translator')
    parser.add_argument('input_file', help='Path to the input configuration file')
    args = parser.parse_args()

    with open(args.input_file, 'r') as file:
        text = file.read()

    lexer = Lexer(text)
    tokens = lexer.tokenize()

    parser = Parser(tokens)
    variables = parser.parse()

    xml_generator = XMLGenerator()
    xml_output = xml_generator.generate_xml(variables)

    print(xml_output)

if __name__ == '__main__':
    main()