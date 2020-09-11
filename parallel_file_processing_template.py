#!/usr/bin/python
#############################################################################
# Some skeleton code for processing lines of a file in parallel
# Gregg Thomas, August 2020
#############################################################################

import multiprocessing as mp

#############################################################################
# Functions
def chunks(l, n):
# Splits a list l into even chunks of size n.
    n = max(1, n);
    return (l[i:i+n] for i in range(0, len(l), n));

###########################

def parallelParse(line_chunk):
    output_lines = [];
    for line in line_chunk:
        # DO YOUR LOOP TO PROCESS LINES IN A FILE HERE
        # DO NOT WRITE TO OUTPUT FILE IN THIS LOOP -- RATHER RETURN THE STRINGS TO WRITE OUTSIDE OF THE FUNCTION

        output_lines.append(output_line);

    return output_lines;

#############################################################################
# Main

if __name__ == '__main__':
# Main is necessary for multiprocessing to work on Windows.

    input_file = "YOUR_INPUT_FILE";
    output_file = "YOUR_OUTPUT_FILE";
    # Your files

    num_procs = "NUMBER_OF_PROCESSORS";
    # CHANGE THIS TO INT
    lines_per_proc = "LINES_TO_PARSE_PER_PROCESSOR"
    # CHANGE THIS TO INT
    chunk_size = num_procs * lines_per_proc;
    # Multi-processing variables. 
    # Increasing number of processes decreases run-time but increases memory usage.
    # Increasing number of lines per process increases memory usage with only slight benefits to run-time.
    # However, don't make lines_per_proc too small -- there is some overhead to calling the parallelParse function, and smaller chunks
    # means more calls to that function

    with open(input_file, "r") as infile, open(output_file, "w") as outfile, mp.Pool(processes=num_procs) as pool:
    # Open the files and start the pool of processes.

        cur_lines, i, i_start = [], 0, 1;
        for line in infile:
            i += 1;
            cur_lines.append(line);
            if len(cur_lines) == chunk_size:
            # When the number of lines we've stored equals the chunk size, we start to process the lines.

                print("Processing lines " + str(i_start) + "-" + str(i));
                i_start = i + 1;
                line_chunks = list(chunks(cur_lines, lines_per_proc));
                # Split up the current chunk into smaller chunks for each process.

                for result in pool.starmap(parallelParse, ((line_chunk) for line_chunk in line_chunks)):
                # You can pass more arguments to parallelParse: pool.starmap(parallelParse, ((line_chunk, arg1, arg2) for line_chunk in line_chunks)):
                # Be sure to make the same change on line 82.
                    for output_line in result:
                        outfile.write(output_line);
                # Call a function that has your loop to process lines of the file with starmap. Starmap should preserve order when outputting.
                # If order is not important, there may be some ways to decrease run-time slightly.

                cur_lines = [];
                # Reset the current chunk of lines.

        if cur_lines != []:
        # Unless the number of lines in the file is an exact multiple of the chunk_size there will be lines left over to process. Do that here.

            print("Processing lines " + str(i_start) + "-" + str(i));
            line_chunks = list(chunks(cur_lines, lines_per_proc));
            # Split up the current chunk into smaller chunks for each process.

            for result in pool.starmap(parallelParse, ((line_chunk) for line_chunk in line_chunks)):
                for output_line in result:
                    outfile.write(output_line);
            # Call a function that has your loop to process lines of the file with starmap. Starmap should preserve order when outputting.
            # If order is not important, there may be some ways to decrease run-time slightly.
