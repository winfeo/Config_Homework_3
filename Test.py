import unittest
import xml.etree.ElementTree as ET
from Main import Lexer, Parser, XMLGenerator

class TestLexer(unittest.TestCase):
    def test_comments(self):
        text = "#=\nThis is a comment\n=#"
        lexer = Lexer(text)
        tokens, comment = lexer.tokenize()
        self.assertEqual(comment.strip(), "This is a comment")

    def test_variable_declaration(self):
        text = "var x = 10;"
        lexer = Lexer(text)
        tokens, comment = lexer.tokenize()
        self.assertEqual(tokens, [('VAR', 'var'), ('IDENTIFIER', 'x'), ('=', '='), ('NUMBER', '10'), (';', ';')])

    def test_string_assignment(self):
        text = 'var name = "Alice";'
        lexer = Lexer(text)
        tokens, comment = lexer.tokenize()
        self.assertEqual(tokens, [('VAR', 'var'), ('IDENTIFIER', 'name'), ('=', '='), ('STRING', 'Alice'), (';', ';')])

class TestParser(unittest.TestCase):
    def test_parse_variable_declaration(self):
        text = "var x = 10;"
        lexer = Lexer(text)
        tokens, _ = lexer.tokenize()
        parser = Parser(tokens)
        variables = parser.parse()
        self.assertEqual(variables, {'x': 10.0})

    def test_parse_string_assignment(self):
        text = 'var name = "Alice";'
        lexer = Lexer(text)
        tokens, _ = lexer.tokenize()
        parser = Parser(tokens)
        variables = parser.parse()
        self.assertEqual(variables, {'name': 'Alice'})

    def test_error_handling(self):
        text = "var x = invalid;"
        lexer = Lexer(text)
        tokens, _ = lexer.tokenize()
        parser = Parser(tokens)
        with self.assertRaises(NameError):
            parser.parse()

class TestIntegration(unittest.TestCase):
    def test_full_program_flow(self):
        # Use a sample input file and verify the output XML
        pass

if __name__ == '__main__':
    unittest.main()