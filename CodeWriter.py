"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import typing
import os

class CodeWriter:
    """Translates VM commands into Hack assembly code."""
    labels_counter = 0

    def __init__(self, output_stream: typing.TextIO) -> None:
        """Initializes the CodeWriter.

        Args:
            output_stream (typing.TextIO): output stream.
        """
        # Note that you can write to output_stream like so:
        # output_stream.write("Hello world! \n")
        self.func_counter = 0
        self.out_file = output_stream
        self.file_name = ""
        self.current_function = ""

    def set_file_name(self, filename: str) -> None:
        """Informs the code writer that the translation of a new VM file is 
        started.

        Args:
            filename (str): The name of the VM file.
        """
        # This function is useful when translating code that handles the
        # static segment. For example, in order to prevent collisions between two
        # .vm files which push/pop to the static segment, one can use the current
        # file's name in the assembly variable's name and thus differentiate between
        # static variables belonging to different files.
        # To avoid problems with Linux/Windows/MacOS differences with regards
        # to filenames and paths, you are advised to parse the filename in
        # the function "translate_file" in Main.py using python's os library,
        # For example, using code similar to:
        # input_filename, input_extension = os.path.splitext(os.path.basename(input_file.name))

        self.file_name, _ = os.path.splitext(os.path.basename(filename))
        # self.file_name = filename

    def write_arithmetic(self, command: str) -> None:
        """Writes assembly code that is the translation of the given 
        arithmetic command. For the commands eq, lt, gt, you should correctly
        compare between all numbers our computer supports, and we define the
        value "true" to be -1, and "false" to be 0.

        Args:
            command (str): an arithmetic command.
        """
        arithmetic_symbols = {"add": "+", "and": "&", "or": "|", "neg": "-",
                              "not": "!", "eq": "JEQ", "gt": "JLT",
                              "lt": "JGT",
                              "shiftleft": "<<", "shiftright": ">>"}

        if command == "add" or command == "and" or command == "or":
            written_command = "@SP\n" \
                                "M=M-1\n" \
                              "A=M\n" \
                              "D=M\n" \
                              "A=A-1\n" \
                              "D=D" + arithmetic_symbols[command] + "M\n" \
                              "M=D\n"
        if command == "sub":
            written_command = "@SP\n" \
                            "M=M-1\n" \
                              "A=M\n" \
                              "D=M\n" \
                              "A=A-1\n" \
                              "D=M-D\n" \
                              "M=D\n"
        elif command == "neg" or command == "not":
            written_command = "@SP\n" \
                              "A=M\n" \
                              "A=A-1\n" \
                              "M=" + arithmetic_symbols[command] + "M\n"
        elif command == "shiftleft" or command == "shiftright":
            written_command = "@SP\n" \
                              "A=M-1\n" \
                              "M=M" + arithmetic_symbols[command] + "\n"
        elif command == "eq" or command == "gt" or command == "lt":
            written_command = \
                            "@SP\n" \
                            "M=M-1\n" \
                            "A=M\n" \
                            "D=M\n" \
                            "@IS_POS" + str(CodeWriter.labels_counter) + "\n" \
                            "D;JGE\n" \
                            "@IS_NEG" + str(CodeWriter.labels_counter) + "\n" \
                            "0;JMP\n" \
                            "(IS_POS" + str(CodeWriter.labels_counter) + ")\n"\
                            "@SP\n"\
                            "A=M-1\n"\
                            "D=M\n"\
                            "@CHECK_ARITH" + str(CodeWriter.labels_counter) + "\n" \
                            "D;JGE\n"\
                            "@SP\n"\
                            "A=M-1 \n"

            if command == "eq" or command == "gt":
                written_command += "M=0 \n"
            if command == "lt":
                written_command += "M=-1 \n"

            written_command +=\
                            "@END" + str(CodeWriter.labels_counter) + "\n"\
                            "0;JMP\n"\
                            "(IS_NEG" + str(CodeWriter.labels_counter) + ")\n"\
                            "@SP\n"\
                            "A=M-1\n"\
                            "D=M\n"\
                            "@CHECK_ARITH" + str(CodeWriter.labels_counter) + "\n"\
                            "D;JLT\n"\
                            "@SP\n"\
                            "A=M-1\n"\

            if command == "eq" or command == "lt":
                written_command += "M=0\n"
            if command == "gt":
                written_command += "M=-1\n"

            written_command += \
                            "@END" + str(CodeWriter.labels_counter) + "\n"\
                            "0;JMP\n"\
                            "(CHECK_ARITH" + str(CodeWriter.labels_counter) + ")\n"\
                            "@SP\n"\
                            "A=M\n"\
                            "D=M\n"\
                            "A=A-1\n"\
                            "D=M-D\n"\
                            "M=-1\n"\
                            "@END" + str(CodeWriter.labels_counter) + "\n"

            if command == "eq":
                written_command += "D;JEQ\n"
            if command == "gt":
                written_command += "D;JGT\n"
            if command == "lt":
                written_command += "D;JLT\n"

            written_command += \
                            "@SP\n"\
                            "A=M\n"\
                            "A=A-1\n"\
                            "M=0\n"\
                            "(END" + str(CodeWriter.labels_counter) + ")\n"

        self.out_file.write(written_command)
        CodeWriter.labels_counter += 1

    def __write_push(self, segment: str, index: int) -> str:
        segment_memory = {"local": "LCL", "argument": "ARG", "this": "THIS",
                          "that": "THAT", "pointer": "THIS", "temp": "5"}

        push_command = "@SP\n" \
                       "A=M\n" \
                       "M=D\n" \
                       "@SP\n" \
                       "M=M+1\n"

        if segment == "constant":
            written_command = "@" + str(index) + "\n" \
                              "D=A\n"
        elif segment == "static":
            written_command = "@" + self.file_name + "." + str(index) + "\n" \
                              "D=M\n"

        elif segment == "pointer":
            if index == 0:
                segment = "this"
            else:
                segment = "that"
            written_command = "@" + segment_memory[segment] + "\n" \
                              "D=M\n"

        elif segment == "this" or segment == "that":
            written_command = "@" + str(index) + "\n" \
                              "D=A\n" \
                              "@" + segment_memory[segment] + "\n" \
                              "A=M+D\n" \
                              "D=M\n"

        elif segment == "temp":
            written_command = "@" + segment_memory[segment] + "\n" \
                              "D=A\n" \
                              "@" + str(index) + "\n" \
                              "A=D+A\n" \
                              "D=M\n"
        else:
            written_command = "@" + str(index) + "\n" \
                              "D=A\n" \
                              "@" + segment_memory[segment] + "\n" \
                              "A=M\n" \
                              "A=A+D\n" \
                              "D=M\n"
        written_command = written_command + push_command
        return written_command

    def __write_pop(self,segment: str, index: int) -> str:
        segment_memory = {"local": "LCL", "argument": "ARG", "this": "THIS",
                          "that": "THAT", "pointer": "THIS", "temp": "5"}

        pop_command = "@SP\n" \
                      "M=M-1\n" \
                      "A=M\n" \
                      "D=M\n"

        if segment == "static":
            written_command = pop_command + \
                              "@" + self.file_name + "." + str(index) + "\n" \
                              "M=D\n"
        elif segment == "pointer":
            if index == 0:
                segment = "this"
            else:
                segment = "that"
            written_command = "@SP\n" \
                              "AM = M-1\n" \
                              "D=M \n" \
                              "@" + segment_memory[segment] + "\n" \
                              "M=D\n"
        elif segment == "temp":
            written_command = "@" + str(index) + "\n" \
                              "D=A\n" \
                              "@" + segment_memory[segment] + "\n" \
                              "D=A+D\n" \
                              "@R13\n" \
                              "M=D\n" + \
                              pop_command + \
                              "@R13\n" \
                              "A=M\n" \
                              "M=D\n"
        else:
            written_command = "@" + str(index) + "\n" \
                              "D=A\n" \
                              "@" + segment_memory[segment] + "\n" \
                              "D=D+M\n" \
                              "@R13\n" \
                              "M=D\n" + \
                              pop_command + \
                              "@R13\n" \
                              "A=M\n" \
                              "M=D\n"
        return written_command

    def write_push_pop(self, command: str, segment: str, index: int) -> None:
        """Writes assembly code that is the translation of the given 
        command, where command is either C_PUSH or C_POP.

        Args:
            command (str): "C_PUSH" or "C_POP".
            segment (str): the memory segment to operate on.
            index (int): the index in the memory segment.
        """
        # Note: each reference to "static i" appearing in the file Xxx.vm should
        # be translated to the assembly symbol "Xxx.i". In the subsequent
        # assembly process, the Hack assembler will allocate these symbolic
        # variables to the RAM, starting at address 16.

        if command == "C_PUSH":
            written_command = self.__write_push(segment, index)
        else:  # C_POP
            written_command = self.__write_pop(segment, index)
        self.out_file.write(written_command)

    def write_label(self, label: str) -> None:
        """Writes assembly code that affects the label command. 
        Let "Xxx.foo" be a function within the file Xxx.vm. The handling of
        each "label bar" command within "Xxx.foo" generates and injects the symbol
        "Xxx.foo$bar" into the assembly code stream.
        When translating "goto bar" and "if-goto bar" commands within "foo",
        the label "Xxx.foo$bar" must be used instead of "bar".

        Args:
            label (str): the label to write.
        """
        written_command = "(" + self.current_function + "$" + label + ")\n"
        self.out_file.write(written_command)

    def write_goto(self, label: str) -> None:
        """Writes assembly code that affects the goto command.

        Args:
            label (str): the label to go to.
        """
        written_command = "@" + self.current_function + "$" + label + "\n"\
                          "0;JMP\n"
        self.out_file.write(written_command)

    def write_if(self, label: str) -> None:
        """Writes assembly code that affects the if-goto command. 

        Args:
            label (str): the label to go to.
        """
        written_command = "@SP\n" \
                          "M=M-1\n" \
                          "A=M\n" \
                          "D=M\n"\
                          "@" + self.current_function + "$" + label + "\n"\
                          "D;JNE\n"  # if D is different than 0"

        self.out_file.write(written_command)

    def __restore_address(self, address: str, index: int) -> str:
        written_command = "@frame\n" \
                          "D=M\n" \
                          "@" + str(index) + "\n" \
                          "D=D-A\n" \
                          "A=D\n" \
                          "D=M\n" \
                          "@" + address + "\n" \
                          "M=D\n"
        return written_command

    def __push_segment_to_stack(self, segment: str) -> str:
        written_command = "@" + segment + "\n" \
                          "D=M\n" \
                          "@SP\n" \
                          "M=M+1\n" \
                          "A=M-1\n" \
                          "M=D\n"

        return written_command

    def write_function(self, function_name: str, n_vars: int) -> None:
        """Writes assembly code that affects the function command. 
        The handling of each "function Xxx.foo" command within the file Xxx.vm
        generates and injects a symbol "Xxx.foo" into the assembly code stream,
        that labels the entry-point to the function's code.
        In the subsequent assembly process, the assembler translates this 
        symbol into the physical address where the function code starts.

        Args:
            function_name (str): the name of the function.
            n_vars (int): the number of local variables of the function.
        """
        # This is irrelevant for project 7,
        # you will implement this in project 8!
        # The pseudo-code of "function function_name n_vars" is:
        # (function_name)       // injects a function entry label into the code
        # repeat n_vars times:  // n_vars = number of local variables
        #   push constant 0     // initializes the local variables to 0
        self.current_function = function_name

        written_command =   "(" + function_name + ")\n" \
                            "@" + str(n_vars) + "\n" \
                            "D=A\n" \
                            "(PUSHZERO" + str(CodeWriter.labels_counter) + ")\n" \
                            "@END" + str(CodeWriter.labels_counter) + "\n" \
                            "D;JEQ\n" \
                            "@SP\n" \
                            "A=M\n" \
                            "M=0\n" \
                            "@SP\n" \
                            "M=M+1\n" \
                            "D=D-1\n" \
                            "@PUSHZERO" + str(CodeWriter.labels_counter) + "\n" \
                            "0;JMP\n" \
                            "(END" + str(CodeWriter.labels_counter) + ")\n"
        self.out_file.write(written_command)
        CodeWriter.labels_counter += 1
        self.func_counter = 0

    def write_call(self, function_name: str, n_args: int) -> None:
        """Writes assembly code that affects the call command. 
        Let "Xxx.foo" be a function within the file Xxx.vm.
        The handling of each "call" command within Xxx.foo's code generates and
        injects a symbol "Xxx.foo$ret.i" into the assembly code stream, where
        "i" is a running integer (one such symbol is generated for each "call"
        command within "Xxx.foo").
        This symbol is used to mark the return address within the caller's 
        code. In the subsequent assembly process, the assembler translates this
        symbol into the physical memory address of the command immediately
        following the "call" command.

        Args:
            function_name (str): the name of the function to call.
            n_args (int): the number of arguments of the function.
        """
        # This is irrelevant for project 7,
        # you will implement this in project 8!
        # The pseudo-code of "call function_name n_args" is:
        # push return_address   // generates a label and pushes it to the stack
        # push LCL              // saves LCL of the caller
        # push ARG              // saves ARG of the caller
        # push THIS             // saves THIS of the caller
        # push THAT             // saves THAT of the caller
        # ARG = SP-5-n_args     // repositions ARG
        # LCL = SP              // repositions LCL
        # goto function_name    // transfers control to the callee
        # (return_address)      // injects the return address label into the code
        return_address = self.current_function + "$ret." + str(self.func_counter)
        written_command = "@" + return_address + "\n" \
                          "D=A\n" \
                          "@SP\n" \
                          "M=M+1\n" \
                          "A=M-1\n" \
                          "M=D\n" + \
                          self.__push_segment_to_stack("LCL") + \
                          self.__push_segment_to_stack("ARG") + \
                          self.__push_segment_to_stack("THIS") + \
                          self.__push_segment_to_stack("THAT") + \
                          "@SP\n" \
                          "D=M\n" \
                          "@5\n" \
                          "D=D-A\n" \
                          "@" + str(n_args) + "\n" \
                          "D=D-A\n" \
                          "@ARG\n" \
                          "M=D\n" \
                          "@SP\n"\
                          "D=M\n" \
                          "@LCL\n" \
                          "M=D\n" \
                          "@" + function_name + "\n" \
                          "0;JMP\n" \
                          "(" + return_address + ")\n"

        self.func_counter += 1
        self.out_file.write(written_command)

    def write_return(self) -> None:
        """Writes assembly code that affects the return command."""
        # This is irrelevant for project 7,
        # you will implement this in project 8!
        # The pseudo-code of "return" is:
        # frame = LCL                   // frame is a temporary variable
        # return_address = *(frame-5)   // puts the return address in a temp var
        # *ARG = pop()                  // repositions the return value for the caller
        # SP = ARG + 1                  // repositions SP for the caller
        # THAT = *(frame-1)             // restores THAT for the caller
        # THIS = *(frame-2)             // restores THIS for the caller
        # ARG = *(frame-3)              // restores ARG for the caller
        # LCL = *(frame-4)              // restores LCL for the caller
        # goto return_address           // go to the return address

        written_command = "@LCL\n" \
                          "D=M\n" \
                          "@frame\n" \
                          "M=D\n" \
                          "@5\n" \
                          "D=A\n" \
                          "@frame\n" \
                          "D=M-D\n" \
                          "A=D\n" \
                          "D=M\n" \
                          "@return_address\n" \
                          "M=D\n" \
                          + self.__write_pop("argument", 0) + \
                          "@ARG\n" \
                          "D=M+1\n" \
                          "@SP\n" \
                          "M=D\n" + \
                          self.__restore_address("THAT", 1) + \
                          self.__restore_address("THIS", 2) + \
                          self.__restore_address("ARG", 3) + \
                          self.__restore_address("LCL", 4) + \
                          "@return_address\n" \
                          "A=M\n" \
                          "0;JMP\n"
        self.out_file.write(written_command)

    def write_boot(self) -> None:
        written_command = "@256\n" \
                          "D=A\n" \
                          "@SP\n" \
                          "M=D\n"

        self.out_file.write(written_command)
        self.write_call("Sys.init", 0)
