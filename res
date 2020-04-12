#!/usr/bin/python
############################################################
# Command line tool for SLURM clusters to check relevant
# resource usage on nodes.
# Parses output of:     scontrol -o show nodes --all
# Usage:
#       res <partition or node name>
#
# If no partition or node name is given, displays 
# info for ALL nodes.
#
# April, 2020
############################################################

import sys, subprocess

pyv = sys.version_info[0];
pyv_long = ".".join(map(str, sys.version_info[:3]))
# Get the python version.

if any(h in sys.argv for h in ['-h', '--h', '--help', '-help', '--usage']):
    sys.exit("\n res: Display resource info for nodes.\n Executing with Python version: " + pyv_long + "\n\n Usage:\n         res <partition or node name>\n\n If no partition or node name is given, displays info for ALL nodes.\n")
# A help/usage message.

if len(sys.argv) > 2:
    sys.exit(" * Error: Unrecognized argument. Please enter only one search term.")
if len(sys.argv) == 2:
    search_str = " | grep " + sys.argv[1];
else:
    search_str = "";
# Parsing input option.

cmd = "scontrol -o show nodes --all" + search_str
if pyv == 2:
    cmd_result = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE);
    stdout, stderr = cmd_result.communicate();
elif pyv == 3:
    cmd_result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE);
    stdout, stderr = cmd_result.stdout.decode(), cmd_result.stderr.decode();
# Run the scontrol command. Syntax is slightly different for python 2 and 3.

if stderr != "":
    print(" * scontrol encountered the following error:")
    print(stderr);
    sys.exit();
# Check if the command returned an error.

nodes = list(filter(None, stdout.split("\n")));
# Get the list of nodes from stdout

col_width = 16;
indent_width = 5
# Spacing options

headers = ["NODE NAME", "CPUs TOTAL", "CPUs ALLOCATED", "CPUs FREE", "TOTAL MEM (MB)", "FREE MEM (MB)", "STATE"];
header = " " * indent_width;
for h in headers:
    num_spaces = col_width - len(h);
    header += h + " " * num_spaces;
print(header);
# Print the header

ordered_cols = ['NodeName', 'CPUTot', 'CPUAlloc', 'CPUFree', 'RealMemory', 'FreeMem', 'State'];
for node in nodes:
    outline = " " * indent_width;
    node_info = {};
    for col in ordered_cols:
        node_info[col] = "NA";

    node = node.split(" ");
    for n in node:
        n = n.split("=");
        if n[0] in ordered_cols:
            node_info[n[0]] = n[1];

    node_info['CPUFree'] = str(int(node_info['CPUTot']) - int(node_info['CPUAlloc']));
    # CPUs free is calculated based on total and allocated CPUs

    for col in ordered_cols:
        num_spaces = col_width - len(node_info[col])
        outline += node_info[col] + " " * num_spaces;

    print(outline);
# Print the info for each node returned from the command.


