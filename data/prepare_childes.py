"""Functions for processing CHAT (.cha) files based on line prefixes.

This module provides functionality to process CHAT format files, specifically
filtering lines that begin with asterisk (*) which typically denote speaker turns.
"""


def process_cha_file(input_file: str, output_file: str) -> None:
    """Read a .cha file and write only lines beginning with '*' to output file.

    Args:
        input_file: Path to the input .cha file to be processed.
        output_file: Path where the processed content will be written.

    Raises:
        FileNotFoundError: If the input file does not exist.
        IOError: If there are issues reading the input or writing to output.
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        processed_lines = [line for line in lines if line.strip().startswith('*')]

        with open(output_file, 'w', encoding='utf-8') as f:
            f.writelines(processed_lines)

        print(f"Successfully processed {input_file}")
        print(f"processed content written to {output_file}")

    except FileNotFoundError:
        print(f"Error: File {input_file} not found")
    except IOError as e:
        print(f"IO error occurred: {str(e)}")


if __name__ == "__main__":

    # Example usage
    input_file = "childes/Eng-NA/Bates/Free20/amy.cha"
    output_file = "childes_prep/output.cha"
    process_cha_file(input_file, output_file)
