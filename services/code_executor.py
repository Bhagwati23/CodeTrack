"""
Secure Code Execution Engine for CodeTrack Pro
Supports Python, Java, C++, and C with sandboxed execution
"""

import os
import sys
import time
import signal
import subprocess
import tempfile
import logging
import resource
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class CodeExecutionError(Exception):
    """Custom exception for code execution errors"""
    pass

class CodeExecutor:
    """Secure code execution engine with sandboxing"""
    
    def __init__(self):
        self.supported_languages = {
            'python': {
                'extension': '.py',
                'command': 'python3',
                'timeout': 5,
                'memory_limit': 128,  # MB
                'template': '#!/usr/bin/env python3\n{code}'
            },
            'java': {
                'extension': '.java',
                'command': 'javac',
                'run_command': 'java',
                'timeout': 10,
                'memory_limit': 256,  # MB
                'template': 'public class Solution {{\n    public static void main(String[] args) {{\n        {code}\n    }}\n}}'
            },
            'cpp': {
                'extension': '.cpp',
                'command': 'g++',
                'timeout': 10,
                'memory_limit': 256,  # MB
                'template': '#include <iostream>\n#include <vector>\n#include <string>\nusing namespace std;\n\nint main() {{\n    {code}\n    return 0;\n}}'
            },
            'c': {
                'extension': '.c',
                'command': 'gcc',
                'timeout': 10,
                'memory_limit': 256,  # MB
                'template': '#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n\nint main() {{\n    {code}\n    return 0;\n}}'
            }
        }
        
        # Security settings
        self.max_execution_time = 5  # seconds
        self.max_memory_usage = 256  # MB
        self.max_output_size = 1024 * 1024  # 1MB
        self.allowed_imports = {
            'python': [
                'math', 'random', 'string', 'collections', 'itertools',
                'heapq', 'bisect', 'sys', 'os', 'json', 'datetime'
            ],
            'java': ['java.util.*', 'java.io.*', 'java.lang.*'],
            'cpp': ['iostream', 'vector', 'string', 'algorithm', 'map', 'set'],
            'c': ['stdio.h', 'stdlib.h', 'string.h', 'math.h']
        }
        
        # Restricted functions/operations
        self.restricted_patterns = [
            r'import\s+subprocess',
            r'import\s+os\.system',
            r'exec\s*\(',
            r'eval\s*\(',
            r'__import__',
            r'open\s*\(',
            r'file\s*\(',
            r'input\s*\(',
            r'raw_input\s*\(',
            r'system\s*\(',
            r'popen\s*\(',
            r'fork\s*\(',
            r'spawn\s*\(',
            r'NetworkRequest',
            r'http\.',
            r'urllib',
            r'socket',
            r'threading',
            r'multiprocessing'
        ]
    
    def execute_code(self, code: str, language: str, test_cases: List[Dict[str, str]], 
                    timeout: Optional[int] = None) -> Dict[str, Any]:
        """Execute code with test cases and return results"""
        
        if language not in self.supported_languages:
            return {"error": f"Unsupported language: {language}"}
        
        # Validate code for security
        security_check = self._validate_code_security(code, language)
        if security_check["blocked"]:
            return {"error": f"Code blocked for security reasons: {security_check['reason']}"}
        
        try:
            # Prepare execution environment
            execution_config = self.supported_languages[language]
            execution_timeout = timeout or execution_config['timeout']
            
            # Create temporary files
            with tempfile.TemporaryDirectory() as temp_dir:
                results = []
                
                # Execute code for each test case
                for i, test_case in enumerate(test_cases):
                    result = self._execute_single_test_case(
                        code, language, test_case, temp_dir, execution_timeout
                    )
                    results.append(result)
                
                # Calculate overall score
                passed_tests = sum(1 for r in results if r['status'] == 'passed')
                total_tests = len(results)
                score = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
                
                return {
                    "status": "completed",
                    "score": score,
                    "passed_tests": passed_tests,
                    "total_tests": total_tests,
                    "results": results,
                    "execution_time": sum(r.get('execution_time', 0) for r in results),
                    "memory_used": max(r.get('memory_used', 0) for r in results) if results else 0
                }
                
        except Exception as e:
            logger.error(f"Code execution failed: {e}")
            return {"error": f"Execution failed: {str(e)}"}
    
    def _execute_single_test_case(self, code: str, language: str, test_case: Dict[str, str],
                                temp_dir: str, timeout: int) -> Dict[str, Any]:
        """Execute code for a single test case"""
        
        start_time = time.time()
        
        try:
            # Prepare code with test case input
            prepared_code = self._prepare_code_with_input(code, language, test_case['input'])
            
            # Create source file
            config = self.supported_languages[language]
            source_file = os.path.join(temp_dir, f"solution{config['extension']}")
            
            with open(source_file, 'w') as f:
                f.write(prepared_code)
            
            # Compile if needed
            if language in ['java', 'cpp', 'c']:
                compile_result = self._compile_code(source_file, language, temp_dir)
                if compile_result['status'] != 'success':
                    return {
                        "status": "compilation_error",
                        "error": compile_result['error'],
                        "execution_time": time.time() - start_time,
                        "memory_used": 0
                    }
            
            # Execute code
            execution_result = self._run_code(source_file, language, temp_dir, timeout)
            execution_time = time.time() - start_time
            
            # Compare output
            expected_output = test_case['expected_output'].strip()
            actual_output = execution_result['output'].strip()
            
            status = 'passed' if self._compare_outputs(actual_output, expected_output) else 'failed'
            
            return {
                "status": status,
                "input": test_case['input'],
                "expected_output": expected_output,
                "actual_output": actual_output,
                "execution_time": execution_time,
                "memory_used": execution_result.get('memory_used', 0),
                "error": execution_result.get('error')
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "execution_time": time.time() - start_time,
                "memory_used": 0
            }
    
    def _prepare_code_with_input(self, code: str, language: str, input_data: str) -> str:
        """Prepare code with test case input"""
        
        if language == 'python':
            # For Python, add input reading at the beginning
            input_lines = input_data.split('\n')
            input_code = "import sys\ninput = sys.stdin.read().strip().split('\\n')\n"
            
            # Add input parsing based on number of lines
            if len(input_lines) == 1:
                input_code += "n = input[0]\n"
            else:
                for i, line in enumerate(input_lines):
                    input_code += f"line{i} = input[{i}]\n"
            
            return input_code + "\n" + code
        
        elif language == 'java':
            # For Java, modify the template to read input
            template = self.supported_languages['java']['template']
            input_reading = f"""
        Scanner scanner = new Scanner(System.in);
        String input = "";
        while (scanner.hasNextLine()) {{
            input += scanner.nextLine() + "\\n";
        }}
        scanner.close();
        
        // Parse input
        String[] lines = input.trim().split("\\\\n");
        
        {code}
"""
            return template.format(code=input_reading)
        
        elif language in ['cpp', 'c']:
            # For C++/C, add input reading
            template = self.supported_languages[language]['template']
            input_reading = f"""
        // Read input
        string input_line;
        vector<string> lines;
        while (getline(cin, input_line)) {{
            lines.push_back(input_line);
        }}
        
        {code}
"""
            return template.format(code=input_reading)
        
        return code
    
    def _compile_code(self, source_file: str, language: str, temp_dir: str) -> Dict[str, Any]:
        """Compile source code"""
        
        config = self.supported_languages[language]
        output_file = os.path.join(temp_dir, "solution")
        
        try:
            if language == 'java':
                cmd = [config['command'], '-d', temp_dir, source_file]
            else:  # cpp, c
                cmd = [config['command'], '-o', output_file, source_file]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                cwd=temp_dir
            )
            
            if result.returncode == 0:
                return {"status": "success", "output_file": output_file}
            else:
                return {"status": "error", "error": result.stderr}
                
        except subprocess.TimeoutExpired:
            return {"status": "error", "error": "Compilation timeout"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _run_code(self, source_file: str, language: str, temp_dir: str, 
                 timeout: int) -> Dict[str, Any]:
        """Run compiled or interpreted code"""
        
        config = self.supported_languages[language]
        
        try:
            if language == 'python':
                cmd = [config['command'], source_file]
            elif language == 'java':
                cmd = ['java', '-cp', temp_dir, 'Solution']
            else:  # cpp, c
                cmd = [os.path.join(temp_dir, 'solution')]
            
            # Set up process with resource limits
            def set_limits():
                # Set memory limit
                memory_limit = config['memory_limit'] * 1024 * 1024  # Convert to bytes
                resource.setrlimit(resource.RLIMIT_AS, (memory_limit, memory_limit))
                
                # Set CPU time limit
                cpu_time_limit = timeout
                resource.setrlimit(resource.RLIMIT_CPU, (cpu_time_limit, cpu_time_limit))
            
            # Run with resource limits
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                preexec_fn=set_limits if os.name != 'nt' else None,  # Windows doesn't support preexec_fn
                cwd=temp_dir
            )
            
            return {
                "output": result.stdout,
                "error": result.stderr if result.stderr else None,
                "return_code": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                "output": "",
                "error": "Execution timeout",
                "return_code": -1
            }
        except Exception as e:
            return {
                "output": "",
                "error": str(e),
                "return_code": -1
            }
    
    def _compare_outputs(self, actual: str, expected: str) -> bool:
        """Compare actual and expected outputs"""
        
        # Normalize whitespace and line endings
        actual_normalized = '\n'.join(line.strip() for line in actual.strip().split('\n'))
        expected_normalized = '\n'.join(line.strip() for line in expected.strip().split('\n'))
        
        # Exact match
        if actual_normalized == expected_normalized:
            return True
        
        # Try numerical comparison for floating point numbers
        try:
            actual_lines = actual_normalized.split('\n')
            expected_lines = expected_normalized.split('\n')
            
            if len(actual_lines) != len(expected_lines):
                return False
            
            for actual_line, expected_line in zip(actual_lines, expected_lines):
                actual_values = actual_line.split()
                expected_values = expected_line.split()
                
                if len(actual_values) != len(expected_values):
                    return False
                
                for actual_val, expected_val in zip(actual_values, expected_values):
                    # Try to compare as numbers
                    try:
                        actual_num = float(actual_val)
                        expected_num = float(expected_val)
                        
                        # Allow small floating point differences
                        if abs(actual_num - expected_num) > 1e-6:
                            return False
                    except ValueError:
                        # Not numbers, compare as strings
                        if actual_val != expected_val:
                            return False
            
            return True
            
        except Exception:
            return False
    
    def _validate_code_security(self, code: str, language: str) -> Dict[str, Any]:
        """Validate code for security issues"""
        
        import re
        
        # Check for restricted patterns
        for pattern in self.restricted_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                return {
                    "blocked": True,
                    "reason": f"Restricted pattern detected: {pattern}"
                }
        
        # Check for dangerous imports
        if language == 'python':
            import_lines = re.findall(r'import\s+(\w+)', code)
            for import_name in import_lines:
                if import_name not in self.allowed_imports['python']:
                    return {
                        "blocked": True,
                        "reason": f"Restricted import: {import_name}"
                    }
        
        # Check code length (prevent extremely long code)
        if len(code) > 10000:  # 10KB limit
            return {
                "blocked": True,
                "reason": "Code too long"
            }
        
        # Check for infinite loops (basic detection)
        loop_patterns = [
            r'while\s*\(\s*True\s*\)',
            r'for\s*\([^)]*\)\s*\{\s*\}',
            r'while\s*\(\s*1\s*\)'
        ]
        
        for pattern in loop_patterns:
            if re.search(pattern, code):
                return {
                    "blocked": True,
                    "reason": "Potential infinite loop detected"
                }
        
        return {"blocked": False}
    
    def get_supported_languages(self) -> Dict[str, Dict[str, Any]]:
        """Get list of supported languages and their configurations"""
        return {
            lang: {
                "extension": config["extension"],
                "timeout": config["timeout"],
                "memory_limit": config["memory_limit"]
            }
            for lang, config in self.supported_languages.items()
        }
    
    def validate_test_case(self, test_case: Dict[str, str]) -> Dict[str, Any]:
        """Validate a test case format"""
        
        required_fields = ['input', 'expected_output']
        
        for field in required_fields:
            if field not in test_case:
                return {"valid": False, "error": f"Missing required field: {field}"}
        
        # Check input/output size limits
        if len(test_case['input']) > 10240:  # 10KB
            return {"valid": False, "error": "Input too large"}
        
        if len(test_case['expected_output']) > 10240:  # 10KB
            return {"valid": False, "error": "Expected output too large"}
        
        return {"valid": True}
    
    def create_sample_test_cases(self, problem_type: str) -> List[Dict[str, str]]:
        """Create sample test cases for different problem types"""
        
        sample_cases = {
            "array_sum": [
                {
                    "input": "3\n1 2 3",
                    "expected_output": "6",
                    "description": "Sum of array elements"
                },
                {
                    "input": "5\n10 20 30 40 50",
                    "expected_output": "150",
                    "description": "Sum of larger array"
                }
            ],
            "two_sum": [
                {
                    "input": "4 2 7 11 15\n9",
                    "expected_output": "0 1",
                    "description": "Basic two sum test case"
                }
            ],
            "fibonacci": [
                {
                    "input": "5",
                    "expected_output": "5",
                    "description": "5th Fibonacci number"
                },
                {
                    "input": "10",
                    "expected_output": "55",
                    "description": "10th Fibonacci number"
                }
            ],
            "binary_search": [
                {
                    "input": "5\n1 3 5 7 9\n3",
                    "expected_output": "1",
                    "description": "Find target in sorted array"
                }
            ]
        }
        
        return sample_cases.get(problem_type, [])

# Global instance
code_executor = CodeExecutor()
