#!/usr/bin/python
############################################################
# Generates commands for the IQtree to make 1 gene tree at
# a time (since I can't get the -T option to work),
# parallelized with GNU Parallel.
# Also makes SLURM script for concatenation and concordance
# analysis.
#
# Input: 
# 1.    Directory with sequence alignments in FASTA format.
#
# Outputs: 
# 1.    A shell script containing IQ-Tree commands (one
#       per line) to generate locus trees.
# 2.    A shell/SLURM script to submit a job that runs the
#       locus commands in parallel with GNU Parallel
# 3.    A shell/SLURM script to submit a job that runs the
#       concatenation and concordance commands using IQ-Tree's
#       internal multi-threading.
# 4.    Output directories for each IQ-Tree run.
#
# SLURM options:
# 1.    Set -tasks to determine number of CPUs for each job.
############################################################

import sys, os, random, string, datetime, argparse

############################################################
# Functions

def runTime(msg=False, writeout=False, printout=True):
# Prints and writes runtime info.
	if msg:
		if not msg.startswith("#"):
			msg = "# " + msg;
		PWS(msg, writeout, printout);

	PWS("# PYTHON VERSION: " + ".".join(map(str, sys.version_info[:3])), writeout, printout)
	PWS("# Script call:    " + " ".join(sys.argv), writeout, printout)
	PWS("# Runtime:        " + datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S"), writeout, printout);
	PWS("# ----------------", writeout, printout);

######################

def PWS(o_line, o_stream=False, std_stream=True):
# Function to print a string AND write it to the file.
	if std_stream:
		print(o_line);
	if o_stream:
		o_stream.write(o_line + "\n");

######################

def spacedOut(string, totlen, sep=" "):
# Adds spaces to the end of a string to make it a given length.
	spaces = sep * (totlen - len(string));
	return string + spaces;

######################

def getRandStr(strlen=6):
# This function generates a random string to add onto the end 
# of tmp files or output directories to avoid possible overwrites.
	return ''.join(random.choice(string.ascii_letters) for m in range(strlen));

############################################################
# Options

parser = argparse.ArgumentParser(description="IQ-Tree command generator");
parser.add_argument("-i", dest="input", help="Directory of input FASTA alignment files.", default=False);
parser.add_argument("-o", dest="output", help="Desired output directory for aligned files. Job name (-n) will be appended to output directory name.", default=False);
parser.add_argument("-b", dest="bootstrap", help="The number of bootstrap replicates to perform. Default: 1000", default="1000");
parser.add_argument("-n", dest="name", help="A short name for all files associated with this job.", default=False);
parser.add_argument("-p", dest="path", help="The path to IQ-Tree. Default: iqtree", default="iqtree");
parser.add_argument("-ext", dest="ext", help="The FASTA file extension of the input alignments. Default: .fa", default=".fa");
parser.add_argument("--overwrite", dest="overwrite", help="If the output directory already exists and you wish to overwrite it, set this option.", action="store_true", default=False);
parser.add_argument("--outname", dest="outname", help="Use the end of the output directory path as the job name.", action="store_true", default=False);
# IO options

parser.add_argument("-part", dest="part", help="SLURM partition option.", default=False);
parser.add_argument("-nodes", dest="nodes", help="SLURM --nodes option.", default="1");
parser.add_argument("-tasks", dest="tasks", help="SLURM --ntasks option.", type=int, default=1);
parser.add_argument("-cpus", dest="cpus", help="SLURM --cpus-per-task option.", type=int, default=1);
parser.add_argument("-mem", dest="mem", help="SLURM --mem option.", type=int, default=0);
parser.add_argument("-email", dest="email", help="SLURM The user email to add to the job scripts for updates.", default=False);
# SLURM options

args = parser.parse_args();

if not args.input or not os.path.isdir(args.input):
    sys.exit( " * Error 1: An input directory must be defined with -i.");
args.input = os.path.abspath(args.input);

if not args.name:
    name = getRandStr();
else:
    name = args.name;

if not args.output:
    sys.exit( " * Error 2: An output directory must be defined with -o.");

args.output = os.path.abspath(args.output);
if args.outname:
    name = os.path.basename(args.output);
if os.path.isdir(args.output) and not args.overwrite:
    sys.exit( " * Error 3: Output directory (-o) already exists! Explicity specify --overwrite to overwrite it and its contents.");

if int(args.bootstrap) < 1000:
    sys.exit(" * Error 4: Bootstrap (-b) must be at least 1000.");
# IO option error checking

if not args.part:
    sys.exit( " * Error 5: -part must be defined as a valid node partition on your clutser.");
# if args.nodes < 1:
#     sys.exit( " * Error 6: -nodes must be a positive integer.");
if args.tasks < 1:
    sys.exit( " * Error 7: -tasks must be a positive integer.");
if args.tasks < 1:
    sys.exit( " * Error 8: -cpus must be a positive integer.");
if args.tasks < 1:
    sys.exit( " * Error 9: -mem must be a positive integer.");
if not args.email:
    sys.exit( " * Error 10: -email must be provided for SLURM updates.");
# SLURM option error checking

pad = 26
cwd = os.getcwd();
# Job vars

job_dir = os.path.join(args.output, "job-files");
locitree_dir = os.path.join(args.output, "loci");
locitree_file = os.path.join(args.output, "loci.treefile");
concat_dir = os.path.join(args.output, "concat");
concord_dir = os.path.join(args.output, "concord");
# Output sub-directories

for d in [args.output, job_dir, locitree_dir, concat_dir, concord_dir]:
    if not os.path.isdir(d):
        print(spacedOut("# Creating directory:", pad) + d);
        os.system("mkdir " + d);
# Creating output directories.

loci_job_file = os.path.join(job_dir, name + "_loci_cmds.sh");
loci_submit_file = os.path.join(job_dir, name + "_loci_submit.sh");
loci_logdir = os.path.join(args.output, "logs");
concat_submit_file = os.path.join(job_dir, name + "_concat_submit.sh");
# Job files

##########################
# Reporting run-time info for records.
with open(loci_job_file, "w") as outfile:
    runTime("#!/bin/bash\n# IQtree command generator", outfile);
    PWS("# IO OPTIONS", outfile);
    PWS(spacedOut("# Input directory:", pad) + args.input, outfile);
    if args.outname:
        PWS(spacedOut("# --outname:", pad) + "Using end of output directory path as job name.", outfile);
    if not args.name and not args.outname:
        PWS("# -n not specified --> Generating random string for job name", outfile);
    PWS(spacedOut("# Job name:", pad) + name, outfile);
    PWS(spacedOut("# Output directory:", pad) + args.output, outfile);
    if args.overwrite:
        PWS(spacedOut("# --overwrite set:", pad) + "Overwriting previous files in output directory.", outfile);
    PWS(spacedOut("# Loci tree directory:", pad) + locitree_dir, outfile);
    #PWS(spacedOut("# Loci tree file:", pad) + locitree_file, outfile);
    PWS(spacedOut("# Concatenation directory:", pad) + concat_dir, outfile);
    PWS(spacedOut("# Concordance directory:", pad) + concord_dir, outfile);
    PWS(spacedOut("# Logfile directory:", pad) + loci_logdir, outfile);
    PWS(spacedOut("# Job file:", pad) + loci_job_file, outfile);
    PWS("# ----------", outfile);
    PWS("# SLURM OPTIONS", outfile);
    PWS(spacedOut("# Loci submit file:", pad) + loci_submit_file, outfile);
    PWS(spacedOut("# Concat submit file:", pad) + concat_submit_file, outfile);
    PWS(spacedOut("# SLURM partition:", pad) + args.part, outfile);
    PWS(spacedOut("# SLURM nodes:", pad) + str(args.nodes), outfile);
    PWS(spacedOut("# SLURM ntasks:", pad) + str(args.tasks), outfile);
    PWS(spacedOut("# SLURM cpus-per-task:", pad) + str(args.cpus), outfile);
    PWS(spacedOut("# SLURM mem:", pad) + str(args.mem), outfile);
    PWS("# ----------", outfile);
    PWS("# BEGIN CMDS", outfile);
    
##########################
# Generating the commands in the job file.
    skipped = 0;
    for f in sorted(os.listdir(args.input)):
        if not f.endswith(args.ext):
            continue;

        base_input = os.path.splitext(f)[0];
        cur_infile = os.path.join(args.input, f);

        cur_outdir = os.path.join(locitree_dir, base_input);
        if not os.path.isdir(cur_outdir):
            os.makedirs(cur_outdir);

        cur_out_prefix = os.path.join(cur_outdir, base_input);
        cur_logfile = os.path.join(loci_logdir, base_input + "-iqtree.log");

        iqtree_cmd = args.path + " -s " + cur_infile + " --prefix " + cur_out_prefix;
        if int(args.bootstrap) > 0:
            iqtree_cmd += " -B " + str(args.bootstrap);
        iqtree_cmd += " -T 1 > " + cur_logfile + " 2>&1";

        outfile.write(iqtree_cmd + "\n");

    #cat_cmd = "cat " + locitree_dir + "/*/*.treefile > " + locitree_file;
    #outfile.write(cat_cmd + "\n");
    # Loci commands

    concat_log = os.path.join(concat_dir, "concat-terminal.log");
    concat_prefix = os.path.join(concat_dir, args.name);
    concat_cmd = "iqtree -p " + args.input + " --prefix " + concat_prefix + " -B 1000 -T " + str(args.cpus) + " &> " + concat_log;
    # Concatenation command

    concord_log = os.path.join(concord_dir, "concord-terminal.log");
    concat_file = os.path.join(concat_dir, args.name + ".treefile");
    concord_prefix = os.path.join(concord_dir, args.name);
    concord_cmd = "iqtree -t " + concat_file + " --gcf " + locitree_file + " -p " + args.input + " --scf 100 --cf-verbose --prefix " + concord_prefix + " -T 1";
    # Concordance command

    PWS("# ----------", outfile);
    PWS(spacedOut("# Files skipped: ", pad) + str(skipped), outfile);
    PWS("# Writing concat commands to " + concat_submit_file, outfile);
    PWS("# " + concat_cmd, outfile);
    PWS("# " + concord_cmd, outfile);

##########################
# Generating the loci submit script.

with open(loci_submit_file, "w") as sfile:
    submit = '''#!/bin/bash
#SBATCH --job-name={name}
#SBATCH --output={name}-%j.out
#SBATCH --mail-type=ALL
#SBATCH --mail-user={email}
#SBATCH --partition={partition}
#SBATCH --nodes={nodes}
#SBATCH --ntasks={tasks}
#SBATCH --cpus-per-task={cpus}
#SBATCH --mem={mem}

parallel -j {tasks} < {output_file}'''

    sfile.write(submit.format(name=name, email=args.email, partition=args.part, nodes=args.nodes, tasks=args.tasks, cpus=args.cpus, mem=args.mem, output_file=loci_job_file));

##########################

##########################
# Generating the concat submit script.

with open(concat_submit_file, "w") as sfile:
    submit = '''#!/bin/bash
#SBATCH --job-name={name}
#SBATCH --output={name}-%j.out
#SBATCH --mail-type=ALL
#SBATCH --mail-user={email}
#SBATCH --partition={partition}
#SBATCH --nodes={nodes}
#SBATCH --ntasks={tasks}
#SBATCH --cpus-per-task={cpus}
#SBATCH --mem={mem}

{concat_cmd}
{concord_cmd}'''

    sfile.write(submit.format(name=name, email=args.email, partition=args.part, nodes=args.nodes, tasks=1, cpus=args.tasks, mem=args.mem, concat_cmd=concat_cmd, concord_cmd=concord_cmd));

##########################