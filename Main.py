import argparse
import re
import sys
import os
import xml.etree.ElementTree as ET

# Лексический анализатор (токенизатор)
class Lexer:
    def __init__(self, text):
        self.text = re.sub(r'\ufeff', '', text)  # Убираем BOM
        self.text = re.sub(r'\xa0', ' ', self.text)  # Заменяем неразрывные пробелы
        self.text = re.sub(r'\u200B', '', self.text)  # Убираем нулевой пробел
        self.tokens = []
        self.pos = 0

    def tokenize(self):
        token_specification = [
            ('NUMBER', r'\d+\.\d*|\d*\.\d+|\d+'),  # Числа с плавающей точкой и целые числа
            ('STRING', r'"[^"]*"'),                # Строки в кавычках
            ('IDENTIFIER', r'[A-Za-zА-Яа-я_][A-Za-zА-Яа-я_0-9]*'),  # Идентификаторы
            ('EXPR', r'@\[[^\]]+\]'),               # Постфиксное выражение
            ('OP', r'[+\-*/]'),                     # Операторы
            ('MOD', r'mod'),                        # Оператор mod
            ('PUNCT', r'[{}:,\[\]]'),               # Специальные символы
            ('ASSIGN', r'='),                       # Оператор присваивания
            ('COMMENT', r'#=[\s\S]*?#=#'),          # Многострочные комментарии
            ('SEMICOLON', r';'),                    # Точка с запятой
            ('SKIP', r'[ \t\n]+'),                  # Пробелы и символы новой строки
            ('MISMATCH', r'.'),                     # Остальное (ошибки)
        ]

        # Собираем регулярные выражения в одно
        tok_regex = '|'.join(f'(?P<{pair[0]}>{pair[1]})' for pair in token_specification)
        get_token = re.compile(tok_regex).match
        pos = 0

        while pos < len(self.text):
            match = get_token(self.text, pos)
            if not match:
                print(f"Не удалось распознать символ: {self.text[pos]}")  # Отладочный вывод
                raise SyntaxError(f'Unexpected character: {self.text[pos]}')

            kind = match.lastgroup
            value = match.group()

            # Пропускаем комментарии
            if kind == 'COMMENT':
                pos = match.end()
                continue  # Игнорируем комментарии, пропускаем к следующему токену

            # Добавляем токены в список
            if kind == 'NUMBER':
                self.tokens.append((kind, value))
            elif kind == 'STRING':
                self.tokens.append((kind, value.strip('"')))
            elif kind == 'IDENTIFIER':
                self.tokens.append((kind, value))
            elif kind == 'EXPR':
                self.tokens.append(('EXPR', value))
            elif kind == 'OP':
                self.tokens.append((kind, value))
            elif kind == 'MOD':
                self.tokens.append((kind, 'mod'))
            elif kind == 'PUNCT':
                self.tokens.append(value)
            elif kind == 'ASSIGN':
                self.tokens.append(('=', '='))  # Присваивание
            elif kind == 'SEMICOLON':  # Обработка точки с запятой
                self.tokens.append(('SEMICOLON', value))
            elif kind == 'SKIP':
                pass  # Игнорируем пробелы
            elif kind == 'MISMATCH':
                raise SyntaxError(f'Unexpected token: {value}')
            pos = match.end()

    def get_tokens(self):
        return self.tokens

# Синтаксический анализатор (парсер)
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.variables = {}

    def parse(self):
        """Запускает процесс парсинга."""
        self.parse_statements()
        return self.variables

    def parse_statements(self):
        """Обрабатывает последовательность заявлений."""
        while self.pos < len(self.tokens):
            token = self.tokens[self.pos]
            if token[0] == 'IDENTIFIER' and token[1] == 'var':
                self.pos += 1
                self.parse_variable_declaration()
            elif token[0] == '{':
                self.pos += 1
                self.variables = self.parse_dictionary()
            else:
                raise SyntaxError(f"Unexpected token: {token}")

    def parse_variable_declaration(self):
        """Обрабатывает объявление переменной."""
        name = self.tokens[self.pos][1]
        self.pos += 1  # Пропустить имя
        if self.tokens[self.pos][0] != '=':
            raise SyntaxError(f"Expected '=' after variable name, got {self.tokens[self.pos]}")
        self.pos += 1  # Пропустить '='
        value = self.parse_value()
        self.variables[name] = value

    def parse_value(self):
        """Обрабатывает значение переменной."""
        token = self.tokens[self.pos]
        if token[0] == 'NUMBER':
            self.pos += 1
            return float(token[1]) if '.' in token[1] else int(token[1])
        elif token[0] == 'STRING':
            self.pos += 1
            return token[1]
        elif token[0] == 'IDENTIFIER':
            self.pos += 1
            return self.variables.get(token[1], None)
        elif token[0] == '{':
            return self.parse_dictionary()
        elif token[0] == '@EXPR':
            return self.parse_postfix_expression()
        else:
            raise SyntaxError(f"Unexpected token: {token}")

    def parse_dictionary(self):
        """Обрабатывает словарь."""
        result = {}
        while self.tokens[self.pos][0] != '}':
            key = self.tokens[self.pos][1]
            self.pos += 1  # Пропустить ключ
            if self.tokens[self.pos][0] != ':':
                raise SyntaxError(f"Expected ':', got {self.tokens[self.pos]}")
            self.pos += 1  # Пропустить ':'
            value = self.parse_value()
            result[key] = value
            if self.tokens[self.pos][0] == ',':
                self.pos += 1  # Пропустить ','
        self.pos += 1  # Пропустить '}'
        return result

    def parse_postfix_expression(self):
        """Обрабатывает постфиксное выражение вида @[число число оператор]."""
        self.pos += 1  # Пропустить '@['
        stack = []
        operators = []

        while self.tokens[self.pos][0] != ']':
            token = self.tokens[self.pos]
            if token[0] == 'NUMBER':
                stack.append(float(token[1]) if '.' in token[1] else int(token[1]))
            elif token[0] in ('+', '-', '*', '/', 'mod'):
                operators.append(token[1])
            else:
                raise SyntaxError(f"Unexpected token in postfix expression: {token}")
            self.pos += 1
        self.pos += 1  # Пропустить ']'

        # Обработка операторов
        while operators:
            self.process_operator(stack, operators.pop(0))

        if len(stack) != 1:
            raise SyntaxError("Invalid postfix expression")
        return stack[0]

    def process_operator(self, stack, operator):
        """Применяет оператор к стеку."""
        if len(stack) < 2:
            raise SyntaxError("Not enough values in stack for operation")
        b = stack.pop()
        a = stack.pop()
        if operator == '+':
            stack.append(a + b)
        elif operator == '-':
            stack.append(a - b)
        elif operator == '*':
            stack.append(a * b)
        elif operator == '/':
            if b == 0:
                raise ZeroDivisionError("Division by zero in postfix expression")
            stack.append(a / b)
        elif operator == 'mod':
            stack.append(a % b)

# Генератор XML
class XMLGenerator:
    def generate_xml(self, variables):
        root = ET.Element("config")
        for key, value in variables.items():
            if isinstance(value, dict):
                self.add_dictionary(root, key, value)
            else:
                root.set(key, str(value))
        return ET.tostring(root, encoding='unicode', method='xml')

    def add_dictionary(self, parent, name, dictionary):
        dict_element = ET.SubElement(parent, "dictionary", name=name)
        for key, value in dictionary.items():
            entry_element = ET.SubElement(dict_element, "entry", name=key)
            if isinstance(value, dict):
                self.add_dictionary(entry_element, key, value)
            else:
                entry_element.set("value", str(value))

# Основная функция
def main():
    parser = argparse.ArgumentParser(description='Configuration Language to XML Translator')
    parser.add_argument('input_file', help='Path to the input configuration file')
    args = parser.parse_args()

    with open(args.input_file, 'r', encoding='utf-8') as file:
        text = file.read()

    # Лексический анализ
    lexer = Lexer(text)
    lexer.tokenize()

    # Парсинг
    parser = Parser(lexer.get_tokens())
    variables = parser.parse()

    # Генерация XML
    xml_generator = XMLGenerator()
    xml_data = xml_generator.generate_xml(variables)

    print(xml_data)

if __name__ == '__main__':
    main()
