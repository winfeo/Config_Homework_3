import argparse
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom

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
                token = self.text[start:self.pos]
                if '.' in token:
                    self.tokens.append(('STRING', token))
                else:
                    self.tokens.append(('NUMBER', token))
            elif self.text[self.pos].isalpha() or self.text[self.pos] == '_':
                start = self.pos
                while self.pos < len(self.text) and (self.text[self.pos].isalnum() or self.text[self.pos] == '_'):
                    self.pos += 1
                token = self.text[start:self.pos]
                if token == 'var':
                    self.tokens.append(('VAR', token))
                elif token == 'mod':
                    self.tokens.append(('MOD', token))
                else:
                    self.tokens.append(('IDENTIFIER', token))
            elif self.text[self.pos] == '"':
                start = self.pos
                self.pos += 1
                while self.pos < len(self.text) and self.text[self.pos] != '"':
                    self.pos += 1
                self.tokens.append(('STRING', self.text[start+1:self.pos]))
                self.pos += 1
            else:
                self.tokens.append((self.text[self.pos], self.text[self.pos]))
                self.pos += 1
        # print("Tokens:", self.tokens)  # Отладочный вывод
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
            current_token = self.tokens[self.pos]
            # print(f"Parsing statement: {current_token}") #отладочная информация
            if current_token[0] == 'VAR':
                self.parse_variable_declaration()
            elif current_token[0] == '{':
                value = self.parse_dictionary()
                self.variables['config'] = value
                return  # Exit after parsing the dictionary
            else:
                raise SyntaxError(f"Unexpected token: {current_token}")

    def parse_variable_declaration(self):
        # print(f"Parsing variable declaration: {self.tokens[self.pos]}") #отладочная информация
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
        # print(f"Parsing value: {self.tokens[self.pos]}") #отладочная информация
        if self.tokens[self.pos][0] == 'NUMBER':
            value = float(self.tokens[self.pos][1])
            self.pos += 1
            return value
        elif self.tokens[self.pos][0] == 'IDENTIFIER':
            if self.tokens[self.pos][1] not in self.variables:
                raise NameError(f"Undefined variable: {self.tokens[self.pos][1]}")
            value = self.variables[self.tokens[self.pos][1]]
            self.pos += 1
            return value
        elif self.tokens[self.pos][0] == 'STRING':
            value = self.tokens[self.pos][1]
            self.pos += 1
            return value
        elif self.tokens[self.pos][0] == '@':
            value = self.parse_postfix_expression()
            return value
        elif self.tokens[self.pos][0] == '{':
            value = self.parse_dictionary()
            return value
        else:
            raise SyntaxError(f"Unexpected token: {self.tokens[self.pos]}")

    def parse_postfix_expression(self):
        # print(f"Parsing postfix expression: {self.tokens[self.pos]}") #отладочная информация
        self.pos += 1  # Skip '@'
        self.pos += 1  # Skip '['
        stack = []
        while self.tokens[self.pos][0] != ']':
            # print(f"Current token: {self.tokens[self.pos]}") #отладочная информация
            # print(f"Stack: {stack}") #отладочная информация
            if self.tokens[self.pos][0] == 'IDENTIFIER':
                ident = self.tokens[self.pos][1]
                if ident not in self.variables:
                    raise NameError(f"Undefined variable: {ident}")
                value = self.variables[ident]
                stack.append(value)
                self.pos += 1
            elif self.tokens[self.pos][0] == 'NUMBER':
                stack.append(float(self.tokens[self.pos][1]))
                self.pos += 1
            elif self.tokens[self.pos][0] in '+-*/':
                if len(stack) < 2:
                    raise SyntaxError("Not enough operands for operator")
                b = stack.pop()
                a = stack.pop()
                if isinstance(a, str) and '.' in a and isinstance(b, (int, float)):
                    # Increment the last octet of the IP address
                    octets = list(map(int, a.split('.')))
                    octets[3] += int(b)
                    if octets[3] > 255:
                        octets[3] = 255
                    a = '.'.join(map(str, octets))
                    stack.append(a)
                    self.pos += 1  # Increment position after processing operator
                elif isinstance(a, (int, float)) and isinstance(b, (int, float)):
                    op = self.tokens[self.pos][0]
                    if op == '+':
                        stack.append(a + b)
                    elif op == '-':
                        stack.append(a - b)
                    elif op == '*':
                        stack.append(a * b)
                    elif op == '/':
                        stack.append(a / b)
                    self.pos += 1
                else:
                    raise TypeError("Unsupported operand types for operation")
            elif self.tokens[self.pos][0] == 'MOD':
                if len(stack) < 2:
                    raise SyntaxError("Not enough operands for mod")
                b = stack.pop()
                a = stack.pop()
                if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
                    raise TypeError("Operands must be numbers for mod operation")
                stack.append(a % b)
                self.pos += 1  # Skip 'mod'
                # Skip '(' and ')' if present
                if self.tokens[self.pos][0] == '(':
                    self.pos += 1
                if self.tokens[self.pos][0] == ')':
                    self.pos += 1
            else:
                raise SyntaxError(f"Unexpected token in postfix expression: {self.tokens[self.pos]}")
        self.pos += 1  # Skip ']'
        if len(stack) != 1:
            raise SyntaxError("Postfix expression did not result in a single value")
        # print(f"Postfix expression result: {stack[0]}") #отладочная информация
        return stack[0]

    def parse_dictionary(self):
        # print(f"Parsing dictionary: {self.tokens[self.pos]}") #отладочная информация
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
        return self.prettify(root)

    def add_dictionary(self, parent, dictionary):
        dict_element = ET.SubElement(parent, "dictionary")
        for key, value in dictionary.items():
            entry_element = ET.SubElement(dict_element, "entry", name=key)
            if isinstance(value, dict):
                self.add_dictionary(entry_element, value)
            else:
                entry_element.set("value", str(value))

    def prettify(self, elem):
        """Возвращает красиво отформатированный XML-строку."""
        rough_string = ET.tostring(elem, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")

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