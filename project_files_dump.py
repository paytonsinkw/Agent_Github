import os

def read_include_file(file_path):
    """Read the list of files from include.txt."""
    try:
        with open(file_path, 'r') as file:
            file_paths = [line.strip() for line in file if line.strip()]
        return file_paths
    except FileNotFoundError:
        print(f"File {file_path} not found.")
        return []

def read_file_contents(file_path):
    """Read the contents of a file."""
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except FileNotFoundError:
        print(f"File {file_path} not found.")
        return ""

def write_to_template_file(output_path, file_contents):
    """Write the collected file contents to the template file."""
    with open(output_path, 'w') as output_file:
        for file_path, contents in file_contents.items():
            output_file.write(f"#file = {file_path}\n")
            output_file.write(contents)
            output_file.write("\n\n")

def main():
    include_file_path = 'data/include.txt'
    output_file_path = 'data/templates/project_files'

    # Step 1: Read the include.txt file
    file_paths = read_include_file(include_file_path)

    # Step 2: Read the contents of each file
    file_contents = {}
    for file_path in file_paths:
        contents = read_file_contents(file_path)
        file_contents[file_path] = contents

    # Step 3: Write to the template file
    write_to_template_file(output_file_path, file_contents)
    print(f"Template file created at {output_file_path}")

if __name__ == "__main__":
    main()